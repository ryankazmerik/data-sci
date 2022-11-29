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
        f"""Exec [mlsInterMiami].[ds].[getProductPropensityModelData] {lkupclientid}"""
    )

    df = pd.read_sql(storedProc, conn)

    conn.commit()
    cursor.close()

    df.shape

    return df


def run(event, context):

    df = get_data_from_SQL(113)

    # choose the features for the stellar base retention model 
    features = [
        'dimCustomerMasterId', 
        'ticketingid', 
        'distance', 
        'seasonYear',
        'events_prior', 
        'attended_prior', 
        'events_last', 
        'attended_last',
        'tenure', 
        'atp_last', 
        'product_current', 
        'product_last'
    ]

    # copy your main dataframe
    df_dataset = df

    # choose the features & train year & test year
    df_dataset = df_dataset[features]
    df_dataset["seasonYear"] = pd.to_numeric(df_dataset["seasonYear"])
    df_dataset = df_dataset.loc[df_dataset["seasonYear"] <= 2022]

    df_train = df_dataset.sample(frac=0.85, random_state=786)
    df_eval = df_dataset.drop(df_train.index)

    df_train.reset_index(drop=True, inplace=True)
    df_eval.reset_index(drop=True, inplace=True)

    # print out the number of records for training and eval
    print('Data for Modeling: ' + str(df_train.shape))
    print('Unseen Data For Predictions: ' + str(df_eval.shape), end="\n\n")

    setup(
        data= df_train, 
        target="product_current", 
        train_size = 0.85,
        data_split_shuffle=True,
        silent=True,
        verbose=False,
        ignore_features=[
            "dimCustomerMasterId",
            "seasonYear",
            "ticketingid"
        ],
        numeric_features=[
            "atp_last",
            "attended_last",
            "attended_prior",
            "distance",
            "events_last",
            "events_prior",
            "tenure" 
        ]
    );
    
    model_matrix = compare_models(
        fold= 10,
        include= ["rf"]
    )

    best_model = create_model(model_matrix)
    final_model = finalize_model(best_model)

    print(f"Season Year Values: {df['seasonYear'].value_counts()}")
    df_inference = df.loc[df["seasonYear"].astype("int") >= 2023]
    df_inference = df_inference.fillna(0)

    df_predictions = predict_model(final_model, data=df_inference)

    df_predictions_fs = df_predictions[df_predictions.Label == "Full Season"]

    df_predictions_fs_new = df_predictions_fs[df_predictions_fs.product_last != "Full Season"]

    s3 = boto3.resource('s3')

    if event["env"] == "dev":
        bucket = "explore-us-curated-data-sci-product-propensity-us-east-1-u8gldf"
    else:
        bucket = "us-curated-data-sci-product-propensity-us-east-1-d2n55o"
    current_date = datetime.today().strftime('%Y-%m-%d')
    path = "/tmp/product-propensity-scores.csv"

    df_predictions.to_csv(path, index=False)
    s3.Bucket(bucket).upload_file(path, f'date={current_date}/mlsintermiami/scores.csv')