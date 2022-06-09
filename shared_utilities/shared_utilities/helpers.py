import awswrangler as wr
import boto3
import json
import pandas as pd
import pyodbc
import psycopg2

from shared_utilities import aws_helpers

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


def get_redshift_awswrangler_data_api_connection(cluster_id, database, db_user):

    cnxn = wr.data_api.redshift.connect(
        cluster_id=cluster_id,
        database=database,
        db_user=db_user
    )

    return cnxn


def get_redshift_awswrangler_temp_connection(cluster_id, database, db_user="admin"):

    cnxn = wr.redshift.connect_temp(
        cluster_identifier=cluster_id,
        database=database,
        user=db_user
    )

    return cnxn


def get_redshift_psycopg2_connection(cluster_id, database, db_user, cluster_endpoint) -> psycopg2._psycopg.connection:
    redshift_client = boto3.client("redshift")
    cluster_credentials = redshift_client.get_cluster_credentials(
        ClusterIdentifier=cluster_id,
        DbUser=db_user,
        DbName=database,
        DbGroups=["admin_group"],
        AutoCreate=True,
    )
    database_connection = psycopg2.connect(
        host=cluster_endpoint,
        port=5439,
        user=cluster_credentials["DbUser"],
        password=cluster_credentials["DbPassword"],
        database=database,
    )
    return database_connection


def get_retention_model_dataset(cluster_id, database, lkupclientid, start_year, end_year, temp_cursor_name, db_user="admin"):
    
    #get_retention_model_dataset should call this proc in RedShift:
    # ds.getretentionmodeldata(11, 2010, 2021, 'temp_cursor');
    # Where params are: lkupclientid, start_year, end_year, temp cursor name
    #Return a dataframe

    # call SP to get full retention model dataset

    # filter by start year and end year
    #?????????? Does this mean sort by? Or something else? The stored proc would already be *filtered* by those, but not sorted

    return "TODO: Implement this helper"


def get_event_propensity_model_dataset(environment, start_year, end_year):

    # call SP to get full event propensity dataset

    # filter by start year and end year

    return "TODO: Implement this helper"


def get_product_propensity_model_dataset(cluster_id, database, lkupclientid, start_year, end_year, temp_cursor_name, cluster_endpoint, cluster_name = "qa-app", db_user="admin"):

    cnxn = get_redshift_psycopg2_connection(cluster_id, database, db_user, cluster_endpoint)
    
    stored_procedure_query = f"""CALL {database}.ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, '{temp_cursor_name}');"""
    print(stored_procedure_query)

    cursor = cnxn.cursor()
    cursor.execute(stored_procedure_query)

    temp_cursor = cnxn.cursor('temp_cursor')
    data = temp_cursor.fetchall()

    cols = [row[0] for row in temp_cursor.description]
    df_results = pd.DataFrame(data=data, columns=cols)
    print(df_results)

    cnxn.commit()
    cnxn.close()

    return df_results



def get_product_propensity_model_dataset_with_wrangler_temp(cluster_id, database, lkupclientid, start_year, end_year, temp_cursor_name, cluster_endpoint, cluster_name = "qa-app", db_user="admin"):

    stored_procedure_query = f"""CALL {database}.ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, '{temp_cursor_name}');"""
    print(stored_procedure_query)

    conn = get_redshift_awswrangler_temp_connection(cluster_id, database)
    with conn.cursor() as cursor:
        cursor.execute(stored_procedure_query)
        data = cursor.fetchall()
        print(data)
    conn.close()


def get_product_propensity_model_dataset_with_wrangler(cluster_id, database, lkupclientid, start_year, end_year, temp_cursor_name, cluster_endpoint, cluster_name = "qa-app", db_user="admin"):

    stored_procedure_query = f"""CALL {database}.ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, '{temp_cursor_name}');"""
    print(stored_procedure_query)

    conn = wr.redshift.connect(secret_id="app_redshift_qa")
    with conn.cursor() as cursor:
        cursor.execute(stored_procedure_query)
        data = cursor.fetchall()
        print(data)
    conn.close()

#if __name__ == "__main__":

#    c = get_mssql_connection("PRD")

#    print(c)