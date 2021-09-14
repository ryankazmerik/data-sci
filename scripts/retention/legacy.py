import datetime
import numpy as np
import pandas as pd
import psycopg2
import pyodbc
import sys
import xgboost as xgb
import warnings

from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, make_scorer
from sklearn.model_selection import GridSearchCV  # cross validation
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.metrics import plot_confusion_matrix
from sshtunnel import open_tunnel
from pymongo import MongoClient

if not sys.warnoptions:
    warnings.simplefilter("ignore")


def run_training(teamproductyear_id):

    # connecting to Redshift
    conn = psycopg2.connect(
        dbname="dsprod",
        host="sagemaker.cbpdnejrkweo.us-east-1.redshift.amazonaws.com",
        port=5439,
        user="admin",
        password="QCxaxQrpijap79XX6TiX",
        sslmode="require",
    )

    cur2 = conn.cursor()
    sample_query_1 = f"""select teamproductyearid,lkupclientid,clientcode,productgrouping,trainseasonyear,testseasonyear from ds.productyear_all r where teamproductyearid ={teamproductyear_id} ;"""
    bnew = cur2.execute(sample_query_1)
    pnew = cur2.fetchall()
    dfparam = pd.DataFrame(pnew)
    new_columns_param = [
        "teamproductyearid",
        "lkupclientid",
        "clientcode",
        "productgrouping",
        "trainseasonyear",
        "testseasonyear",
    ]
    dfparam3 = pd.DataFrame(pnew, columns=new_columns_param)
    dfparam3.head()

    paramindex = 0

    client_id = dfparam3._get_value(0, "lkupclientid")
    client_code = dfparam3._get_value(0, "clientcode")
    product_grouping = dfparam3._get_value(0, "productgrouping")
    train_season_year = dfparam3._get_value(0, "trainseasonyear")
    test_season_year = dfparam3._get_value(0, "testseasonyear")

    print(
        "\n\n",
        client_id,
        client_code,
        product_grouping,
        train_season_year,
        test_season_year,
        end="\n\n\n",
    )

    cur = conn.cursor()
    sample_query = f"""select r.dimcustomermasterid,recency,attendancePercent,totalSpent,distToVenue,source_tenure,renewedBeforeDays,missed_games_1,missed_games_2,missed_games_over_2,isnextyear_buyer,isnextyear_samepkg_buyer,pkgupgrade_status from ds.retentionscoring r where lkupclientid ={client_id} and productgrouping in({"'"+ str(product_grouping) + "'"}) and year<{train_season_year};"""
    b = cur.execute(sample_query)
    p = cur.fetchall()
    df = pd.DataFrame(p)
    new_columns = [
        "dimcustomermasterid",
        "recency",
        "attendancePercent",
        "totalSpent",
        "distToVenue",
        "source_tenure",
        "renewedBeforeDays",
        "missed_games_1",
        "missed_games_2",
        "missed_games_over_2",
        "isnextyear_buyer",
        "isnextyear_samepkg_buyer",
        "pkgupgrade_status",
    ]
    df3 = pd.DataFrame(p, columns=new_columns)
    df3.drop(["isnextyear_samepkg_buyer", "pkgupgrade_status"], axis=1, inplace=True)
    df3.head()

    df3.count()

    df3["dimcustomermasterid"] = pd.to_numeric(df3["dimcustomermasterid"])
    df3["attendancePercent"] = pd.to_numeric(df3["attendancePercent"])
    df3["totalSpent"] = pd.to_numeric(df3["totalSpent"])
    df3["distToVenue"] = pd.to_numeric(df3["distToVenue"])

    X = df3.drop(["isnextyear_buyer"], axis=1).copy()
    X.head()

    y = df3["isnextyear_buyer"].copy()
    y.head()

    y.unique()

    sum(y) / len(y)

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
    )
    clf.fit(
        X,
        y,
        verbose=False,
        early_stopping_rounds=10,
        eval_metric="aucpr",
        eval_set=[(X, y)],
    )

    # check Important features
    feature_importances_df = pd.DataFrame(
        {"feature": list(X.columns), "importance": clf.feature_importances_}
    ).sort_values("importance", ascending=False)

    # Display
    feature_importances_df

    feature_importances = feature_importances_df[["feature", "importance"]]
    feature_importances["productgrouping"] = product_grouping
    feature_importances = feature_importances[["feature", "importance"]]
    feature_importances.drop([0], axis=0, inplace=True)
    feature_importances

    feature_importance_dict = {}
    for ind in feature_importances.index:
        feature_importance_dict[feature_importances["feature"][ind]] = float(
            feature_importances["importance"][ind]
        )

    connection = MongoClient(
        "mongodb://sean:monstertruck1@52.54.218.77:28001/?authMechanism=SCRAM-SHA-1"
    )
    # connection
    # for x in (connection.views.views_meta_data.find_one()):
    db = connection["views"]
    collection = db["views_meta_data"]
    myquery = {"_id": client_code}
    tenant_doc = collection.find_one(myquery)
    today = datetime.datetime.now()
    if "date_last_retention_scores" not in tenant_doc:
        tenant_doc["date_last_retention_scores"] = {}
    tenant_doc["date_last_retention_scores"] = today
    collection.update_one(myquery, {"$set": tenant_doc}, upsert=True)

    if "attributes_std" not in tenant_doc:
        tenant_doc["attributes_std"] = {}
    tenant_doc["attributes_std"][product_grouping] = feature_importance_dict
    collection.update_one(myquery, {"$set": tenant_doc}, upsert=True)

    # Importing the data
    cur = conn.cursor()
    sample_query2 = f"""select r.dimcustomermasterid,recency,attendancePercent,totalSpent,distToVenue,source_tenure,renewedBeforeDays,missed_games_1,missed_games_2,missed_games_over_2,isnextyear_buyer,isnextyear_samepkg_buyer,pkgupgrade_status from ds.retentionscoring r where lkupclientid ={client_id} and productgrouping in({"'"+ str(product_grouping) + "'"}) and year={test_season_year};"""
    b2 = cur.execute(sample_query2)
    p2 = cur.fetchall()
    df_test2 = pd.DataFrame(p2)
    new_columns_test = [
        "dimcustomermasterid",
        "recency",
        "attendancePercent",
        "totalSpent",
        "distToVenue",
        "source_tenure",
        "renewedBeforeDays",
        "missed_games_1",
        "missed_games_2",
        "missed_games_over_2",
        "isnextyear_buyer",
        "isnextyear_samepkg_buyer",
        "pkgupgrade_status",
    ]
    df_test = pd.DataFrame(p2, columns=new_columns)
    df_test.drop(
        ["isnextyear_samepkg_buyer", "pkgupgrade_status"], axis=1, inplace=True
    )
    df_test.head()

    df_test.count()

    df_test["dimcustomermasterid"] = pd.to_numeric(df_test["dimcustomermasterid"])
    df_test["attendancePercent"] = pd.to_numeric(df_test["attendancePercent"])
    df_test["totalSpent"] = pd.to_numeric(df_test["totalSpent"])
    df_test["distToVenue"] = pd.to_numeric(df_test["distToVenue"])

    X_test = df_test.drop(["isnextyear_buyer"], axis=1).copy()
    X_test.head()

    y_pred = clf.predict_proba(X)

    # make predictions for test data
    y_pred_test = clf.predict_proba(X_test)

    # Creating the array to convert
    array_y_pred_test = np.array(y_pred_test)

    # Create the dataframe
    df_y_pred_test = pd.DataFrame(array_y_pred_test)
    df_y_pred_test.columns = ["nonbuyer", "buyer"]

    result_test = pd.concat([df_y_pred_test, X_test], axis=1, join="inner")
    # result_test

    result_test = result_test.drop(["nonbuyer"], axis=1).copy()

    result_test["buyer"] = pd.to_numeric(result_test["buyer"])

    today = datetime.datetime.now()
    date_time = today.strftime("%m-%d-%Y %H:%M:%S")

    newscors = result_test[["dimcustomermasterid", "buyer"]]
    newscors.columns = ["dimcustomermasterid", "buyer_score"]
    newscors["year"] = test_season_year
    newscors["lkupclientid"] = client_id
    newscors["productgrouping"] = product_grouping
    newscors["insertDate"] = date_time
    # newscors

    # connect to SQL Server.
    server = "34.206.73.189"
    database = "datascience"
    username = "nrad"
    password = "83F25619-D272-4660-98A2-93AF5CC18D59"
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
    for index, row in newscors.iterrows():
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
    cnxn.commit()
    cursor.close()

    mongoscores = newscors[
        ["dimcustomermasterid", "buyer_score"]
    ]  # dimcustomermasterid
    mongoscores["id_tenant"] = client_code
    mongoscores["productgrouping"] = product_grouping
    mongoscores["year"] = test_season_year
    mongoscores["insertDate"] = datetime.datetime.now()
    mongoscores.columns = [
        "customerNumber",
        "score",
        "id_tenant",
        "productgrouping",
        "year",
        "date",
    ]
    mongoscores_dict = mongoscores.to_dict(orient="records")
    # mongoscores_dict
    # mongoscores.to_numpy()

    feature_importancesdict = feature_importances.to_dict(orient="records")
    feature_importancesdict
    # aa = {feature_importancesdict['feature']: feature_importancesdict['importance']}
    aa = [
        {sample_dict["feature"]: sample_dict["importance"]}
        for sample_dict in feature_importancesdict
    ]
    result = {}
    for d in aa:
        result.update(d)
    # result

    ## test
    final_list = []
    for single_dict in mongoscores_dict:
        temp_dict = {}
        temp_dict2 = {}
        temp_dict["customerNumber"] = single_dict["customerNumber"]
        temp_dict["id_tenant"] = single_dict["id_tenant"]
        temp_dict["productgrouping"] = single_dict["productgrouping"]
        temp_dict["year"] = single_dict["year"]
        temp_dict2 = {
            "score": single_dict["score"],
            "date": single_dict["date"],
            "attribute": result,
        }
        temp_dict["history"] = temp_dict2
        final_list.append(temp_dict)

    # final_list

    connection = MongoClient(
        "mongodb://sean:monstertruck1@52.54.218.77:28001/?authMechanism=SCRAM-SHA-1"
    )
    # connection
    db = connection["views"]
    collection = db["scores_retention"]
    for i in final_list:
        myquery = {
            "customerNumber": i["customerNumber"],
            "id_tenant": i["id_tenant"],
            "product": i["productgrouping"],
            "year": i["year"],
        }
        tenant_doc = collection.find_one(myquery)

        if tenant_doc is None:
            myquery = {
                "customerNumber": i["customerNumber"],
                "id_tenant": i["id_tenant"],
                "product": i["productgrouping"],
                "year": i["year"],
                "history": [i["history"]],
            }
            collection.insert_one(myquery)

        else:

            tenant_doc["history"].append(i["history"])
            collection.update_one(myquery, {"$set": tenant_doc}, upsert=True)

    feature_importances2 = feature_importances
    feature_importances2

    feature_importances2.at[1, "feature"] = "Recency"
    feature_importances2.at[2, "feature"] = "Attendance"
    feature_importances2.at[3, "feature"] = "Monetary"
    feature_importances2.at[4, "feature"] = "Distance to Venue"
    feature_importances2.at[5, "feature"] = "Tenure"
    feature_importances2.at[6, "feature"] = "Time to Renew"
    feature_importances2.at[7, "feature"] = "Missed Games Streak 1"
    feature_importances2.at[8, "feature"] = "Missed Games Streak 2"
    feature_importances2.at[9, "feature"] = "Missed Games Streak Over 2"
    feature_importances2

    today = datetime.datetime.now()
    date_time = today.strftime("%m-%d-%Y %H:%M:%S")

    feature_importances2["attrank"] = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    feature_importances2["lkupClientId"] = client_id
    feature_importances2["modelVersnNumber"] = 2
    feature_importances2["scoreDate"] = date_time
    feature_importances2["loadId"] = 0
    feature_importances2["product"] = product_grouping
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
    feature_importances2

    # connect to SQL Server.
    server = "34.206.73.189"
    database = "datascience"
    username = "nrad"
    password = "83F25619-D272-4660-98A2-93AF5CC18D59"
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
    # cursor.execute("INSERT INTO dbo.finalscore (dimcustomermasterid,buyer_score,lkupclientid,insertDate) values(1,1,1,null)")
    for index, row in feature_importances2.iterrows():
        cursor.execute(
            "INSERT INTO stlrMILB.dw.lkupRetentionAttributeImportance (attribute,product,indexValue,rank,lkupClientId,modelVersnNumber,scoreDate,loadId) values("
            + "'"
            + str(row.attribute)
            + "'"
            + ","
            + "'"
            + str(product_grouping)
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
        # cursor.execute("INSERT INTO stlrMLS.dw.lkupRetentionAttributeImportance (attribute,product,indexValue,rank,lkupClientId,modelVersnNumber,scoreDate,loadId) values(" + "'" +str(row.attribute)+"'"+","+ "'"+str(product_grouping)+"'" +"," + str(round(row.indexValue,4)) + "," + str(row.attrank)+ ","+ str(row.lkupClientId) + "," + str(row.modelVersnNumber)+ "," +str(row.scoreDate) + ","+ str(row.loadId)  + ")")
    cnxn.commit()
    cursor.close()


# teamproductyear_id = 32  # 1,2...74
# 18,19,20, 24, 25, 26 no data for testing

if __name__ == "__main__":

    team_set = [71, 72, 73, 74]

    for id in team_set:

        try:
            run_training(id)
            print("RETENTION SCORING COMPLETED FOR:", id, end="\n\n")

        except Exception as err:
            print(err)
            print("RETENTION SCORING FAILED FOR:", id, end="\n\n")