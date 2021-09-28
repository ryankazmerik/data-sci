import boto3
import datetime
import json
import numpy as np
import pandas as pd
import pyodbc
import sys
import xgboost as xgb
import warnings

from pymongo import MongoClient
from xgboost.training import train

if not sys.warnoptions:
    warnings.simplefilter("ignore")

DATE_TIME = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")

ssm_client = boto3.client("ssm", "us-east-1")
response = ssm_client.get_parameter(
    Name="/product/ai/notebook/db-connections/LEGACY-MSSQL-QA-VPC-WRITE",
    WithDecryption=True,
)["Parameter"]["Value"]
conn = json.loads(response)

#override SSM server IP to public IP
conn['server'] = "52.44.171.130"

print(conn)

CNXN = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server}"
    + ";SERVER="
    + conn["server"]
    + ";DATABASE="
    + conn["database"]
    + ";UID="
    + conn["username"]
    + ";PWD="
    + conn["password"]
)

# NOTE: SSM Parameter timing out on MSSQL connection : need to use internal IP??
# NOTE: dsAdminWrite can't read params
# NOTE: get df_train & df_test from single data pull
# NOTE: consolidate SQL cnxn's - only use dsAdminWrite
# NOTE: refactor feature_importances2 code
# NOTE: reformat insert statements
# NOTE: add inline documentation
# NOTE: add print & log statements to each function
# NOTE: add error handling for no test data (2021 data)


def get_params(teamproductyear_id):

    # query sql for parameters
    cursor = CNXN.cursor()
    query = f"""
        SELECT 
            teamproductyearid,
            lkupclientid,
            clientcode,
            productgrouping,
            trainseasonyear,
            testseasonyear,
            facttestprevyear,
            stlrDBName 
        FROM 
            ds.productyear_all r 
        WHERE 
            teamproductyearid ={teamproductyear_id} ;
        
        """

    # create a dictionary of parameters
    df_params = pd.read_sql(query, CNXN).to_dict("records")[0]

    CNXN.commit()
    cursor.close()

    print(df_params)
    print()

    return df_params


def get_datasets(df_params):

    cust_database = df_params["stlrDBName"]

    cnxn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + SERVER
        + ";DATABASE="
        + cust_database
        + ";UID="
        + USERNAME
        + ";PWD="
        + PASSWORD
    )
    cursor2 = cnxn2.cursor()
    # Prepare the stored procedure execution script and parameter values
    storedProc = f"""Exec [ds].[getRetentionScoringModelData] {client_id}"""
    params = client_id
    cnxn.commit()
    cursor2.close()

    dftrain = pd.read_sql(storedProc, cnxn2)

    dfproduct = dftrain[dftrain["productGrouping"] == product_grouping]

    dfproduct["year"] = pd.to_numeric(dfproduct["year"])

    dfyear = dfproduct[dfproduct["year"] < train_season_year]

    df3 = dfyear[
        [
            "dimCustomerMasterId",
            "recency",
            "attendancePercent",
            "totalSpent",
            "distToVenue",
            "source_tenure",
            "renewedBeforeDays",
            "missed_games_1",
            "missed_games_2",
            "missed_games_over_2",
            "isNextYear_Buyer",
        ]
    ]

    df3.head()

    df3["dimCustomerMasterId"] = pd.to_numeric(df3["dimCustomerMasterId"])
    df3["attendancePercent"] = pd.to_numeric(df3["attendancePercent"])
    df3["totalSpent"] = pd.to_numeric(df3["totalSpent"])
    df3["distToVenue"] = pd.to_numeric(df3["distToVenue"])

    X = df3.drop(["isNextYear_Buyer"], axis=1).copy()
    y = df3["isNextYear_Buyer"].copy()

    return df_train, df_test, df_target


def get_train_dataset(df_params):

    # GET DATA FROM MSSQL
    cursor = CNXN.cursor()

    query = f"""
        SELECT 
            r.dimcustomermasterid,
            recency,
            attendancePercent,
            totalSpent,
            distToVenue,
            source_tenure,
            renewedBeforeDays,
            missed_games_1,
            missed_games_2,
            missed_games_over_2,
            isnextyear_buyer
        FROM 
            ds.retentionscoring r 
        WHERE 
            lkupclientid = {df_params['lkupclientid']} 
        AND 
            productgrouping = {"'"+ df_params['productgrouping'] + "'"} 
        AND 
            year < {df_params["trainseasonyear"]};
        """

    df = pd.read_sql(query, CNXN)

    CNXN.commit()
    cursor.close()

    df["dimcustomermasterid"] = pd.to_numeric(df["dimcustomermasterid"])
    df["attendancePercent"] = pd.to_numeric(df["attendancePercent"])
    df["totalSpent"] = pd.to_numeric(df["totalSpent"])
    df["distToVenue"] = pd.to_numeric(df["distToVenue"])

    df_train = df.drop(["isnextyear_buyer"], axis=1).copy()
    df_target = df["isnextyear_buyer"].copy()

    return df_train, df_test, df_target


def create_model(df_train, df_target):

    clf = xgb.XGBClassifier(
        objective="binary:logistic",
        seed=42,
        gamma=0.25,
        lear_rate=0.1,
        max_depth=6,
        reg_lambda=20,
        scale_pos_weight=3,
        subsample=0.9,
        colsample_bytree=0.5,
        verbosity=0,
    )

    clf.fit(
        df_train,
        df_target,
        verbose=False,
        early_stopping_rounds=10,
        eval_metric="aucpr",
        eval_set=[(df_train, df_target)],
    )

    # check Important features
    feature_importances_df = pd.DataFrame(
        {"feature": list(df_train.columns), "importance": clf.feature_importances_}
    ).sort_values("importance", ascending=False)

    feature_importances = feature_importances_df[["feature", "importance"]]
    feature_importances["productgrouping"] = df_params["productgrouping"]

    feature_importances = feature_importances[["feature", "importance"]]
    feature_importances.drop([0], axis=0, inplace=True)

    feature_importances2 = feature_importances

    feature_importances2.at[1, "feature"] = "Recency"
    feature_importances2.at[2, "feature"] = "Attendance"
    feature_importances2.at[3, "feature"] = "Monetary"
    feature_importances2.at[4, "feature"] = "Distance to Venue"
    feature_importances2.at[5, "feature"] = "Tenure"
    feature_importances2.at[6, "feature"] = "Time to Renew"
    feature_importances2.at[7, "feature"] = "Missed Games Streak 1"
    feature_importances2.at[8, "feature"] = "Missed Games Streak 2"
    feature_importances2.at[9, "feature"] = "Missed Games Streak Over 2"

    feature_importances2["attrank"] = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    feature_importances2["lkupClientId"] = df_params["lkupclientid"]
    feature_importances2["modelVersnNumber"] = 2
    feature_importances2["scoreDate"] = DATE_TIME
    feature_importances2["loadId"] = 0
    feature_importances2["product"] = df_params["productgrouping"]
    feature_importances2.columns = [
        "attribute",
        "indexValue",
        "attrank",
        "lkupClientId",
        "modelVersnNumber",
        "scoreDate",
        "loadId",
        "product",
    ]

    return clf, feature_importances2


def get_test_dataset(df_params):

    cursor = CNXN.cursor()

    query = f"""
        SELECT 
            r.dimcustomermasterid,
            recency,
            attendancePercent,
            totalSpent,
            distToVenue,
            source_tenure,
            renewedBeforeDays,
            missed_games_1,
            missed_games_2,
            missed_games_over_2,
            isnextyear_buyer
        FROM 
            ds.retentionscoring r 
        WHERE 
            lkupclientid ={df_params['lkupclientid']} 
        AND 
            productgrouping in({"'"+ str(df_params['productgrouping']) + "'"}) 
        AND 
            year={df_params['testseasonyear']} ;"""

    df_test = pd.read_sql(query, CNXN)

    CNXN.commit()
    cursor.close()

    df_test["dimcustomermasterid"] = pd.to_numeric(df_test["dimcustomermasterid"])
    df_test["attendancePercent"] = pd.to_numeric(df_test["attendancePercent"])
    df_test["totalSpent"] = pd.to_numeric(df_test["totalSpent"])
    df_test["distToVenue"] = pd.to_numeric(df_test["distToVenue"])

    df_test = df_test.drop(["isnextyear_buyer"], axis=1).copy()

    return df_test


def calc_retention_scores(df_params, df_test, clf):

    # make predictions for test data
    y_pred_test = clf.predict_proba(df_test)

    # Creating the array to convert
    array_y_pred_test = np.array(y_pred_test)

    # Create the dataframe
    df_y_pred_test = pd.DataFrame(array_y_pred_test)
    df_y_pred_test.columns = ["nonbuyer", "buyer"]

    result_test = pd.concat([df_y_pred_test, df_test], axis=1, join="inner")
    # result_test

    result_test = result_test.drop(["nonbuyer"], axis=1).copy()

    result_test["buyer"] = pd.to_numeric(result_test["buyer"])

    newscors = result_test[["dimcustomermasterid", "buyer"]]
    newscors.columns = ["dimcustomermasterid", "buyer_score"]
    newscors["year"] = df_params["testseasonyear"]
    newscors["lkupclientid"] = df_params["lkupclientid"]
    newscors["productgrouping"] = df_params["productgrouping"]
    newscors["insertDate"] = DATE_TIME

    return newscors


def write_retention_scores(df_params, retention_scores):

    server = "52.44.171.130"
    database = "datascience"
    username = "nrad"
    password = "ThisIsQA123"
    cnxn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + server
        + ";DATABASE="
        + database
        + ";UID="
        + username
        + ";PWD="
        + password
    )

    cursor = cnxn.cursor()

    # Insert Dataframe into SQL Server:
    for index, row in retention_scores.iterrows():
        cursor.execute(
            "INSERT INTO ds.finalscore (dimcustomermasterid,buyer_score,year,lkupclientid,productgrouping,insertDate) values("
            + str(row.dimcustomermasterid)
            + ","
            + str(round(row.buyer_score, 4))
            + ","
            + str(row.year)
            + ","
            + str(row.lkupclientid)
            + ","
            + "'"
            + str(row.productgrouping)
            + "'"
            + ","
            + "'"
            + str(row.insertDate)
            + "'"
            + ")"
        )

    CNXN.commit()
    cursor.close()


def write_feature_importances(df_params, feature_importances):

    server = "52.44.171.130"
    database = "datascience"
    username = "nrad"
    password = "ThisIsQA123"
    cnxn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + server
        + ";DATABASE="
        + database
        + ";UID="
        + username
        + ";PWD="
        + password
    )

    cursor = cnxn.cursor()

    for index, row in feature_importances.iterrows():
        cursor.execute(
            "INSERT INTO stlrMILB.dw.lkupRetentionAttributeImportance (attribute,product,indexValue,rank,lkupClientId,modelVersnNumber,scoreDate,loadId) values("
            + "'"
            + str(row.attribute)
            + "'"
            + ","
            + "'"
            + str(df_params["productgrouping"])
            + "'"
            + ","
            + str(round(row.indexValue, 4))
            + ","
            + str(row.attrank)
            + ","
            + str(row.lkupClientId)
            + ","
            + str(row.modelVersnNumber)
            + ","
            + "'"
            + str(row.scoreDate)
            + "'"
            + ","
            + str(row.loadId)
            + ")"
        )

    cnxn.commit()
    cursor.close()


if __name__ == "__main__":

    teams = [
        # {"clientcode": "66ers", "teamproductyear_ids": [18, 19, 20]},
        {"clientcode": "bulls", "teamproductyear_ids": [4, 5, 6, 7]},
        {"clientcode": "drive", "teamproductyear_ids": [63, 64, 65, 66]},
        {"clientcode": "elpaso", "teamproductyear_ids": [41, 42, 43]},
        # {"clientcode": "fireflies", "teamproductyear_ids": [38, 39, 40]},
        {"clientcode": "grizzlies", "teamproductyear_ids": [34, 35, 36, 37]},
        {"clientcode": "hartfordyardgoats", "teamproductyear_ids": [53, 54]},
        # {"clientcode": "hops", "teamproductyear_ids": [1, 2, 3, 96]},
        # {"clientcode": "indyindians", "teamproductyear_ids": [24, 25, 26]},
        {"clientcode": "kanecounty", "teamproductyear_ids": [71, 72]},
        {"clientcode": "knights", "teamproductyear_ids": [55, 56, 57]},
        {"clientcode": "legends", "teamproductyear_ids": [33]},
        {"clientcode": "loons", "teamproductyear_ids": [21, 22, 23]},
        # {"clientcode": "okcdodgers", "teamproductyear_ids": [58, 59, 60, 61, 62]},
        {"clientcode": "ports", "teamproductyear_ids": [30, 31, 32]},
        {"clientcode": "rainiers", "teamproductyear_ids": [15, 16, 17]},
        {"clientcode": "rattlers", "teamproductyear_ids": [27, 28, 29]},
        {"clientcode": "renoaces", "teamproductyear_ids": [47, 48, 49, 50]},
        {"clientcode": "rivercats", "teamproductyear_ids": [8, 9, 10, 11]},
        {"clientcode": "rrexpress", "teamproductyear_ids": [44, 45, 46]},
        {"clientcode": "stormchasers", "teamproductyear_ids": [51, 52]},
        # {"clientcode": "stripers", "teamproductyear_ids": [67, 68, 69, 70]},
        {"clientcode": "toledomudhens", "teamproductyear_ids": [73, 74]},
        {"clientcode": "vegas51s", "teamproductyear_ids": [12, 13, 14]},
    ]

    for team in teams:

        teamproductyear_ids = team["teamproductyear_ids"]
        for teamproductyear_id in teamproductyear_ids:

            df_params = get_params(teamproductyear_id)
            # print("\n", df_params, end="\n\n")

            # df_train, df_test, df_target = get_datasets(df_params)
            # print(df_train.head(), end="\n\n")
            # print(df_test.head(), end="\n\n")
            # print(df_target.head(), end="\n\n")

            # model, feature_importances = create_model(df_train, df_target)
            # # print(model, end="\n\n")
            # # print(feature_importances, end="\n\n")

            # df_test = get_test_dataset(df_params)
            # # print(df_test, end="\n\n")

            # retention_scores = calc_retention_scores(df_params, df_test, model)
            # # print(retention_scores, end="\n\n")

            # write_retention_scores(df_params, retention_scores)

            # write_feature_importances(df_params, feature_importances)
            print()

    # print("~ Fin ~", end="\n\n")
