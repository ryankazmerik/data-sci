import awswrangler
import boto3
import json
import pyodbc

def hello_world():
    
    msg = "Hello World"
    
    return msg


def get_mssql_connection(environment):

    if environment == "QA":
        env = "LEGACY-MSSQL-QA-VPC-WRITE"
        serv = "52.44.171.130"
    elif environment == "PRD":
        env = "LEGACY-MSSQL-PROD-PRODUCT-WRITE"
        serv = "34.206.73.189"

    ssm_client = boto3.client("ssm", "us-east-1")
    response = ssm_client.get_parameter(
        Name=f"/product/ai/notebook/db-connections/{env}",
        WithDecryption=True,
    )["Parameter"]["Value"]
    sql_connection = json.loads(response)

    cnxn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="+serv
        + ";DATABASE="+sql_connection["database"]
        + ";UID="+sql_connection["username"]
        + ";PWD="+sql_connection["password"]
    )

    return cnxn


def get_redshift_connection(environment):

    # create connection to RedShift API

    return "TODO: Implement this helper"


def get_retention_model_dataset(environment, start_year, end_year):

    # call SP to get full retention model dataset

    # filter by start year and end year

    return "TODO: Implement this helper"


def get_event_propensity_model_dataset(environment, start_year, end_year):

    # call SP to get full event propensity dataset

    # filter by start year and end year

    return "TODO: Implement this helper"


def get_product_propensity_model_dataset(environment, start_year, end_year):

    # call SP to get full product propensity dataset

    # filter by start year and end year

    return "TODO: Implement this helper"


#if __name__ == "__main__":

#    c = get_mssql_connection("PRD")

#    print(c)