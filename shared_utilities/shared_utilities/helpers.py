import boto3
import json
import pyodbc

def hello_world():
    
    msg = "Hello World"
    
    return msg


def get_mssql_connection():

    ssm_client = boto3.client("ssm", "us-east-1")
    response = ssm_client.get_parameter(
        Name=f"/customer/model-retention/ai/db-connections/data-sci-retention/database-write",
        WithDecryption=True,
    )["Parameter"]["Value"]
    sql_connection = json.loads(response)

    cnxn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="
        + sql_connection["server"]
        + ";DATABASE="
        + sql_connection["database"]
        + ";UID="
        + sql_connection["username"]
        + ";PWD="
        + sql_connection["password"]
    )

    return cnxn