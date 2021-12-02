import boto3
import json
import pandas as pd
import pyodbc

def handler(event, context):

     # get db connection from SSM
    ssm_client = boto3.client("ssm", "us-east-1")
    response = ssm_client.get_parameter(
        Name=f"/product/ai/notebook/db-connections/LEGACY-MSSQL-QA-VPC-WRITE",
        WithDecryption=True,
    )["Parameter"]["Value"]
    CONN = json.loads(response)
    
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
    storedProc = f"""Exec [DS].[Run_factCustomerRetention_Full_LOAD] """

    df = pd.read_sql(storedProc, CNXN)

    print(df.info())

    CNXN.commit()
    cursor.close()