import boto3
import getpass
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime
from pycaret.classification import *


def get_data_from_SQL(lkupclientid: int):
    
    ssm_client = boto3.client("ssm")
    client_reponse = ssm_client.get_parameter(Name="/data-sci/data-sci-dw/db_connection", WithDecryption=True)
    conn = pyodbc.connect(client_reponse["Parameter"]["Value"])

    cursor = conn.cursor()

    storedProc = (
        f"""Exec [mlsInterMiami].[ds].[getRetentionScoringModelData] {lkupclientid} """
    )

    df = pd.read_sql(storedProc, conn)

    # apply some data transformations
    df["year"] = pd.to_numeric(df["year"])

    conn.commit()
    cursor.close()

    return df


def run(event, context):

    df = get_data_from_SQL(113)
    
    # choose the features for the stellar base retention model
    features = [
                "dimCustomerMasterId",
                "email",
                "ticketingid",
                "year",
                "productGrouping", 
                "totalSpent", 
                "recentDate",
                "attendancePercent", 
                "renewedBeforeDays",
                "source_tenure",
                "tenure",
                "distToVenue",
                "recency",
                "missed_games_1",
                "missed_games_2",
                "missed_games_over_2",
                "isNextYear_Buyer"
    ]

    # copy your main dataframe
    df_dataset = df

    # choose the features & train year & test year
    df_dataset = df_dataset[features]
    df_dataset["year"] = pd.to_numeric(df_dataset["year"])
    df_dataset = df_dataset.loc[df_dataset["year"] <= 2021]

    df_train = df_dataset.sample(frac=0.85, random_state=786)
    df_eval = df_dataset.drop(df_train.index)

    df_train.reset_index(drop=True, inplace=True)
    df_eval.reset_index(drop=True, inplace=True)

    # print out the number of records for training and eval
    print('Data for Modeling: ' + str(df_train.shape))
    print('Unseen Data For Predictions: ' + str(df_eval.shape), end="\n\n")

    setup(
        data= df_train, 
        target="isNextYear_Buyer", 
        train_size = 0.85,
        data_split_shuffle=True,
        ignore_features=["dimCustomerMasterId","email","productGrouping","ticketingid","year"],
        silent=True,
        verbose=False,
        numeric_features=[
        "totalSpent", 
                "attendancePercent", 
                "renewedBeforeDays",
                "source_tenure",
                "tenure",
                "distToVenue",
                "recency",
                "missed_games_1",
                "missed_games_2",
                "missed_games_over_2"
        ]
    )

    model_matrix = compare_models(
        fold=10,
        include=["lightgbm"]
    )

    lightgbm_model = create_model('lightgbm')

    df_inference = df.loc[df["year"] >= 2022]
    df_inference = df_inference.fillna(0)

    lightgbm_predictions = predict_model(lightgbm_model, data=df_inference, raw_score=True)
    
    pd.set_option('display.max_columns', None)  

    print(f"Lightgbm info:\n {lightgbm_predictions.info()}")

    print(f"lightgbm:\n {lightgbm_predictions.Label.value_counts()}")

    print(f"lightgbm:\n {lightgbm_predictions.Score_1.value_counts(bins=[0, 0.25, 0.5, 0.75, 1])}")

    model_predictions = [lightgbm_predictions]

    current_date = datetime.today().strftime('%Y-%m-%d')
    df_output = pd.DataFrame()
    df_output["attendancepercentage"] = lightgbm_predictions["attendancePercent"]
    df_output["clientcode"] = "mlsintermiami"
    df_output["dimcustomermasterid"] = lightgbm_predictions["dimCustomerMasterId"]
    df_output["email"]= lightgbm_predictions["email"]
    df_output["lkupclientid"] = 113
    df_output["mostrecentattendance"] = lightgbm_predictions["recentDate"]
    df_output["product"] = lightgbm_predictions["productGrouping"]
    df_output["sascore"] = lightgbm_predictions["Score_1"]
    df_output["scoredate"] = current_date
    df_output["seasonyear"] = lightgbm_predictions["year"]
    df_output["tenuredays"] = lightgbm_predictions["tenure"]
    df_output["ticketingid"] = lightgbm_predictions["ticketingid"]

    s3 = boto3.resource('s3')

    if event["env"] == "dev":
        bucket = "explore-us-curated-data-sci-retention-us-east-1-ut8jag"
    else:
        bucket = "us-curated-data-sci-retention-us-east-1-5h6cml"
    
    current_date = datetime.today().strftime('%Y-%m-%d')
    path = "/tmp/retention-scores.csv"

    df_output.to_csv(path, index=False)
    # s3.Bucket(bucket).upload_file(path, f'date={current_date}/mlsintermiami/scores.csv')
    s3.Bucket(bucket).upload_file(path, f'testpleaseignore/mlsintermiami/scores.csv')