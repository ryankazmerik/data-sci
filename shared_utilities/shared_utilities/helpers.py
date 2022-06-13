import awswrangler as wr
import boto3
import json
import pandas as pd
import pyodbc
import psycopg2
import redshift_connector

from shared_utilities import aws_helpers

def hello_world():
    
    msg = "Hello World"
    
    return msg


def get_mssql_connection(environment):
    """Return a pyodbc connection to MSSQL.

    https://github.com/mkleehammer/pyodbc
    """

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


def get_redshift_awswrangler_temp_connection(cluster_id: str, database: str, db_user: str = "admin") -> redshift_connector.Connection:
    """Return a redshift_connector temporary connection (No password required). This has different functionality than psycopg2, such as not having named cursors.

    https://github.com/aws/amazon-redshift-python-driver
    """

    cnxn = wr.redshift.connect_temp(
        cluster_identifier=cluster_id,
        database=database,
        user=db_user
    )

    return cnxn


def get_redshift_psycopg2_connection(cluster_id: str, database: str, db_user: str, cluster_endpoint: str) -> psycopg2._psycopg.connection:
    """Returns a psycopg2 connection, requires full database connection details (user, pass, cluster, database, port, etc).

    https://github.com/psycopg/psycopg2
    """

    redshift_client = boto3.client("redshift")
    cluster_credentials = redshift_client.get_cluster_credentials(
        ClusterIdentifier=cluster_id,
        DbUser=db_user,
        DbName=database,
        DbGroups=["admin_group"],
        AutoCreate=True,
    )
    cnxn = psycopg2.connect(
        host=cluster_endpoint,
        port=5439,
        user=cluster_credentials["DbUser"],
        password=cluster_credentials["DbPassword"],
        database=database,
    )

    return cnxn


def _execute_and_fetch_stored_proc_with_redshift_connector(conn: redshift_connector.Connection, stored_procedure_query, temp_cursor_name):
    """Runs a stored proc and fetches the return value from its temp cursor. 
    
    This function is exlcusively for the redshift_connector, this will not work for pyodbc.
    """
    
    with conn.cursor() as cursor:

        cursor.execute(stored_procedure_query)
        cursor.execute(f"FETCH ALL FROM {temp_cursor_name};")
        data = cursor.fetchall()
        cols = [row[0] for row in cursor.description]
        df_results = pd.DataFrame(data=data, columns=cols)
        
    return df_results


def get_retention_model_dataset(cluster_id: str, database: str, lkupclientid: int, start_year: int, end_year: int, temp_cursor_name: str) -> pd.DataFrame:
    """Runs and returns the results of the following stored procedure: 
    
    `{database}.ds.getretentionmodeldata({lkupclientid}, {start_year}, {end_year}, {temp_cursor_name})`
    """    

    stored_procedure_query = f"""CALL {database}.ds.getretentionmodeldata({lkupclientid}, {start_year}, {end_year}, '{temp_cursor_name}');"""
    conn = get_redshift_awswrangler_temp_connection(cluster_id, database)

    df_results = _execute_and_fetch_stored_proc_with_redshift_connector(conn, stored_procedure_query, temp_cursor_name)

    conn.close()

    return df_results


def get_event_propensity_model_dataset(environment, start_year, end_year):

    # call SP to get full event propensity dataset

    # filter by start year and end year

    return "TODO: Implement this helper"


def get_product_propensity_model_dataset(cluster_id: str, database: str, lkupclientid: int, start_year: int, end_year: int, temp_cursor_name: str) -> pd.DataFrame:
    """Runs and returns the results of the following stored procedure: 
    
    `{database}.ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, {temp_cursor_name})`
    """    

    stored_procedure_query = f"""CALL {database}.ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, '{temp_cursor_name}');"""
    conn = get_redshift_awswrangler_temp_connection(cluster_id, database)

    df_results = _execute_and_fetch_stored_proc_with_redshift_connector(conn, stored_procedure_query, temp_cursor_name)

    conn.close()

    return df_results


#if __name__ == "__main__":

#    c = get_mssql_connection("PRD")

#    print(c)