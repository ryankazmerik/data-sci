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
# NOTE: add dynamic feature engineering


def get_team_dataset(team):

    CNXN = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="
        + CONN["server"]
        + ";DATABASE="
        + team["stlrDBName"]
        + ";UID="
        + CONN["username"]
        + ";PWD="
        + CONN["password"]
    )

    cursor = CNXN.cursor()
    storedProc = (
        f"""Exec [ds].[getRetentionScoringModelData] {team["lkupclientid"]}"""
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

    return df



def get_product_datasets(df, features, product):

    # create df_train filtered by product and train year
    df_train = df[
        (df["productGrouping"] == product["type"])
        & (df["year"] < product["train_year"])
    ]

    # select features for the dataframe
    df_train = df[features]

    # create df_target filtered by product and train year
    df_target = df_train["isNextYear_Buyer"].copy()

    # drop columns from df_train not needed for training
    df_train = df_train.drop(["isNextYear_Buyer", "productGrouping", "year"], axis=1)

    # create df_test and filter by selected features
    df_test = df[features]

    # drop columns from df_test not needed for testing
    df_test = df_test.drop(["isNextYear_Buyer", "productGrouping", "year"], axis=1).copy()
    df_test.reset_index(drop=True, inplace=True)

    return df_train, df_target, df_test



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
    feature_importances["productgrouping"] = product

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
    feature_importances2["product"] = product
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

    # get params for each team
    teams_config = open("../retention/team_config.json")
    params = json.load(teams_config)

    # iterate through each team
    for team in params['teams']:

        # get full datasets for each team
        df = get_team_dataset(team)   

        # get filtered datasets for each product
        for product in team['products']:

            features = team['features']
            
            # get train, target and test dataframes for each product
            df_train, df_target, df_test = get_product_datasets(df, features, product)

            model, feature_importances = create_model(df_train, df_target)
            print(model, end="\n\n")
            print(feature_importances, end="\n\n")

                # retention_scores = calc_retention_scores(df_params, df, df_test, model)
                # # print(retention_scores, end="\n\n")

                # write_retention_scores(df_params, retention_scores)

                # write_feature_importances(df_params, feature_importances)

    print("\n~ Fin ~", end="\n\n")