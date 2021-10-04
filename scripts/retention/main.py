import datetime
import json
import numpy as np
import pandas as pd
import pyodbc
import ssm_helpers
import sys
import xgboost as xgb
import warnings

if not sys.warnoptions:
    warnings.simplefilter("ignore")

DATE_TIME = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")

CONN = json.loads(ssm_helpers.get_param("/product/ai/notebook/db-connections/LEGACY-MSSQL-QA-VPC-WRITE"))

# override SSM server IP to public IP (for local testing)
CONN["server"] = "52.44.171.130"

# NOTE: refactor feature_importances2 code
# NOTE: reformat insert statements
# NOTE: add inline documentation & print statements
# NOTE: add error handling for no test data (2021 data)


def get_params(teamproductyear_id):

    CNXN = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="
        + CONN["server"]
        + ";DATABASE="
        + CONN["database"]
        + ";UID="
        + CONN["username"]
        + ";PWD="
        + CONN["password"]
    )

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
            facttestyear,
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

    return df_params


def get_features(df_params):

    features = [
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
        "year",
        "productGrouping",
    ]
    
    df_features = pd.DataFrame(features, columns = ['Features'])

    return df_features


def get_datasets(df_params, df_features):

    CNXN = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="
        + CONN["server"]
        + ";DATABASE="
        + df_params["stlrDBName"]
        + ";UID="
        + CONN["username"]
        + ";PWD="
        + CONN["password"]
    )

    cursor = CNXN.cursor()
    storedProc = (
        f"""Exec [ds].[getRetentionScoringModelData] {df_params['lkupclientid']}"""
    )

    df = pd.read_sql(storedProc, CNXN)

    CNXN.commit()
    cursor.close()



    # apply some data type transformations
    df["year"] = pd.to_numeric(df["year"])
    df["dimCustomerMasterId"] = pd.to_numeric(df["dimCustomerMasterId"])
    df["attendancePercent"] = pd.to_numeric(df["attendancePercent"])
    df["totalSpent"] = pd.to_numeric(df["totalSpent"])
    df["distToVenue"] = pd.to_numeric(df["distToVenue"])

    # create df_train filtered by product and train year

    df = df[
        (df["productGrouping"] == df_params["productgrouping"])
        & (df["year"] < df_params["trainseasonyear"])
    ]

    df_train = df

    df_train = df_train[df_features["Features"]]

    # create df_target filtered by product and train year
    df_target = df_train["isNextYear_Buyer"].copy()

    # drop columns from df_train not needed for training
    df_train = df_train.drop(["isNextYear_Buyer", "productGrouping", "year"], axis=1)

    # create df_test filtered by product and test year
    df_test = df

    df_test = df_test[df_features["Features"]]

    # drop columns from df_test not needed for testing
    df_test = df_test.drop(
        ["isNextYear_Buyer", "productGrouping", "year"], axis=1
    ).copy()
    df_test.reset_index(drop=True, inplace=True)

    return df, df_train, df_target, df_test


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


def calc_retention_scores(df_params, df, df_test, clf):

    # make predictions for test data
    y_pred_test = clf.predict_proba(df_test)

    # Creating the array to convert
    array_y_pred_test = np.array(y_pred_test)

    # Create the dataframe
    df_y_pred_test = pd.DataFrame(array_y_pred_test)
    df_y_pred_test.columns = ["nonbuyer", "buyer"]

    result_test = pd.concat([df_y_pred_test, df], axis=1, join="inner")

    result_test = result_test.drop(["nonbuyer"], axis=1).copy()

    result_test["buyer"] = pd.to_numeric(result_test["buyer"])
    merged_inner = pd.merge(
        left=result_test,
        right=df_test,
        how="inner",
        left_on="dimCustomerMasterId",
        right_on="dimCustomerMasterId",
    )

    newscors = merged_inner[
        [
            "dimCustomerMasterId",
            "buyer",
            "source_tenure_x",
            "attendancePercent_x",
            "recentDate",
        ]
    ]
    newscors.columns = [
        "dimCustomerMasterId",
        "buyer_score",
        "tenuredays",
        "attendancePercentage",
        "mostrecentattendance",
    ]
    newscors["year"] = df_params["testseasonyear"]
    newscors["lkupclientid"] = df_params["lkupclientid"]
    newscors["productgrouping"] = df_params["productgrouping"]
    newscors["currVersnFlag"] = 1
    newscors["loadid"] = 0
    newscors["seasonyear"] = df_params["facttestyear"]
    newscors["insertDate"] = DATE_TIME

    return newscors


def write_retention_scores(df_params, retention_scores):

    CNXN = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="
        + CONN["server"]
        + ";DATABASE="
        + CONN["database"]
        + ";UID="
        + CONN["username"]
        + ";PWD="
        + CONN["password"]
    )

    cursor = CNXN.cursor()

    # Insert Dataframe into SQL Server:
    for index, row in retention_scores.iterrows():
        cursor.execute(
            "INSERT INTO ds.customerScores (dimCustomerMasterId,buyer_score,tenuredays,attendancePercentage,mostrecentattendance,year,lkupclientid,productgrouping,seasonYear,insertDate) values("
            + str(row.dimCustomerMasterId)
            + ","
            + str(round(row.buyer_score, 4))
            + ","
            + str(row.tenuredays)
            + ","
            + str(row.attendancePercentage)
            + ","
            + "'"
            + str(row.mostrecentattendance)
            + "'"
            + ","
            + str(row.year)
            + ","
            + str(row.lkupclientid)
            + ","
            + "'"
            + str(row.productgrouping)
            + "'"
            + ","
            + str(df_params["facttestyear"])
            + ","
            + "'"
            + str(row.insertDate)
            + "'"
            + ")"
        )

    CNXN.commit()
    cursor.close()


def write_feature_importances(df_params, feature_importances):

    CNXN = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="
        + CONN["server"]
        + ";DATABASE="
        + CONN["database"]
        + ";UID="
        + CONN["username"]
        + ";PWD="
        + CONN["password"]
    )

    cursor = CNXN.cursor()

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

    CNXN.commit()
    cursor.close()


if __name__ == "__main__":

    teams = [
        # {"clientcode": "tester", "teamproductyear_ids": [7]},
        # {"clientcode": "66ers", "teamproductyear_ids": [18, 19, 20]},
        {"clientcode": "bulls", "teamproductyear_ids": [4, 5, 6, 7]},
        # {"clientcode": "drive", "teamproductyear_ids": [63, 64, 65, 66]},
        # {"clientcode": "elpaso", "teamproductyear_ids": [41, 42, 43]},
        # # {"clientcode": "fireflies", "teamproductyear_ids": [38, 39, 40]},
        # {"clientcode": "grizzlies", "teamproductyear_ids": [34, 35, 36, 37]},
        # {"clientcode": "hartfordyardgoats", "teamproductyear_ids": [53, 54]},
        # # {"clientcode": "hops", "teamproductyear_ids": [1, 2, 3, 96]},
        # # {"clientcode": "indyindians", "teamproductyear_ids": [24, 25, 26]},
        # {"clientcode": "kanecounty", "teamproductyear_ids": [71, 72]},
        # {"clientcode": "knights", "teamproductyear_ids": [55, 56, 57]},
        # {"clientcode": "legends", "teamproductyear_ids": [33]},
        # {"clientcode": "loons", "teamproductyear_ids": [21, 22, 23]},
        # # {"clientcode": "okcdodgers", "teamproductyear_ids": [58, 59, 60, 61, 62]},
        # {"clientcode": "ports", "teamproductyear_ids": [30, 31, 32]},
        # {"clientcode": "rainiers", "teamproductyear_ids": [15, 16, 17]},
        # {"clientcode": "rattlers", "teamproductyear_ids": [27, 28, 29]},
        # {"clientcode": "renoaces", "teamproductyear_ids": [47, 48, 49, 50]},
        # {"clientcode": "rivercats", "teamproductyear_ids": [8, 9, 10, 11]},
        # {"clientcode": "rrexpress", "teamproductyear_ids": [44, 45, 46]},
        # {"clientcode": "stormchasers", "teamproductyear_ids": [51, 52]},
        # # {"clientcode": "stripers", "teamproductyear_ids": [67, 68, 69, 70]},
        # {"clientcode": "toledomudhens", "teamproductyear_ids": [73, 74]},
        # {"clientcode": "vegas51s", "teamproductyear_ids": [12, 13, 14]},
    ]

    for team in teams:

        teamproductyear_ids = team["teamproductyear_ids"]
        for teamproductyear_id in teamproductyear_ids:

            df_params = get_params(teamproductyear_id)
            print("\n", df_params, end="\n\n")

            df_features = get_features(df_params)

            df, df_train, df_target, df_test = get_datasets(df_params, df_features)
            model, feature_importances = create_model(df_train, df_target)
            # print(model, end="\n\n")
            # print(feature_importances, end="\n\n")

            retention_scores = calc_retention_scores(df_params, df, df_test, model)
            # print(retention_scores, end="\n\n")

            write_retention_scores(df_params, retention_scores)

            write_feature_importances(df_params, feature_importances)

    print("~ Fin ~", end="\n\n")