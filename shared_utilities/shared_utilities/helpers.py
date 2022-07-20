from typing import Tuple
import boto3
import json
import matplotlib.pyplot as plt
import pandas as pd
import pyodbc
import psycopg2
import redshift_connector

boto3.setup_default_session(profile_name='Stellaralgo-DataScienceAdmin')

def hello_world():
    
    msg = "Hello World"
    
    return msg


def get_mssql_connection(environment: str, database: str):
    """Return a pyodbc connection to MSSQL.

    https://github.com/mkleehammer/pyodbc
    """

    if environment == "qa" or environment == "QA":
        env = "LEGACY-MSSQL-QA-VPC-WRITE"
        serv = "52.44.171.130"
    elif environment == "prd" or environment == "PRD" or environment == "prod" or environment == "PROD":
        env = "LEGACY-MSSQL-PROD-PRODUCT-WRITE"
        serv = "34.206.73.189"

    client = boto3.client('ssm')
    
    response = client.get_parameter(
        Name=f"/product/ai/notebook/db-connections/{env}",
        WithDecryption=True,
    )["Parameter"]["Value"]

    sql_connection = json.loads(response)
   
    cnxn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="+serv
        + ";DATABASE="+database
        + ";UID="+sql_connection["username"]
        + ";PWD="+sql_connection["password"]
    )

    return cnxn


def get_redshift_connection(cluster: str, database: str) -> psycopg2._psycopg.connection:
    """Returns a psycopg2 connection, requires full database connection details (user, pass, cluster, database, port, etc).

    https://github.com/psycopg/psycopg2
    """

    client = boto3.client('redshift')

    if cluster == 'qa-app':
        endpoint = 'qa-app.ctjussvyafp4.us-east-1.redshift.amazonaws.com'
    elif cluster == 'prod-app':
        endpoint = 'prod-app.ctjussvyafp4.us-east-1.redshift.amazonaws.com'
    elif cluster == 'qa-app-elbu':
        endpoint = 'qa-app-elbu.ctjussvyafp4.us-east-1.redshift.amazonaws.com'
    elif cluster == 'prod-app-elbu':
        endpoint == 'prod-app-elbu.ctjussvyafp4.us-east-1.redshift.amazonaws.com'

    cluster_credentials = client.get_cluster_credentials(
        ClusterIdentifier=cluster,
        DbUser='admin',
        DbName=database,
        DbGroups=["admin_group"],
        AutoCreate=True
    )
    cnxn = psycopg2.connect(
        host=endpoint,
        port=5439,
        user=cluster_credentials["DbUser"],
        password=cluster_credentials["DbPassword"],
        database=database
    )

    return cnxn



# def _execute_and_fetch_stored_proc_with_redshift_connector(conn: redshift_connector.Connection, stored_procedure_query, temp_cursor_name):
#     """Runs a stored proc and fetches the return value from its temp cursor. 
    
#     This function is exlcusively for the redshift_connector, this will not work for pyodbc.
#     """
    
#     with conn.cursor() as cursor:

#         cursor.execute(stored_procedure_query)
#         cursor.execute(f"FETCH ALL FROM {temp_cursor_name};")
#         data = cursor.fetchall()
#         cols = [row[0] for row in cursor.description]
#         df_results = pd.DataFrame(data=data, columns=cols)
        
#     return df_results


# def get_retention_model_dataset(cluster_id: str, database: str, lkupclientid: int, start_year: int, end_year: int, temp_cursor_name: str) -> pd.DataFrame:
#     """Runs and returns the results of the following stored procedure: 
    
#     `{database}.ds.getretentionmodeldata({lkupclientid}, {start_year}, {end_year}, {temp_cursor_name})`
#     """    

#     stored_procedure_query = f"""CALL {database}.ds.getretentionmodeldata({lkupclientid}, {start_year}, {end_year}, '{temp_cursor_name}');"""
#     conn = get_redshift_awswrangler_temp_connection(cluster_id, database)

#     df_results = _execute_and_fetch_stored_proc_with_redshift_connector(conn, stored_procedure_query, temp_cursor_name)

#     conn.close()

#     return df_results


# def get_event_propensity_model_dataset(environment, start_year, end_year):

#     # call SP to get full event propensity dataset

#     # filter by start year and end year

#     return "TODO: Implement this helper"


# def get_product_propensity_model_dataset(cluster_id: str, database: str, lkupclientid: int, start_year: int, end_year: int, temp_cursor_name: str) -> pd.DataFrame:
#     """Runs and returns the results of the following stored procedure: 
    
#     `{database}.ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, {temp_cursor_name})`
#     """    

#     stored_procedure_query = f"""CALL {database}.ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, '{temp_cursor_name}');"""
#     conn = get_redshift_awswrangler_temp_connection(cluster_id, database)

#     df_results = _execute_and_fetch_stored_proc_with_redshift_connector(conn, stored_procedure_query, temp_cursor_name)

#     conn.close()

#     return df_results


# def get_train_eval_split(df: pd.DataFrame, random_state: int, train_fraction: float = 0.85) -> Tuple[pd.DataFrame, pd.DataFrame]:
#     """Splits a given DataFrame into train and eval DataFrames.

#     Example:
#     ```
#     df_train, df_eval = helpers.get_train_eval_split(full_df, 123)
#     ```

#     Args:
#         df (pd.DataFrame): DataFrame to be split.
#         random_state (int): Seed to randomize the split functions output.
#         train_fraction (float, optional): The size of the training DataFrame after splitting. Defaults to 0.85.

#     Returns:
#         Tuple[pd.DataFrame, pd.DataFrame]: The split DataFrames.
#     """
    
#     df_train = df.sample(frac=train_fraction, random_state=random_state)
#     df_eval = df.drop(df_train.index)

#     df_train.reset_index(drop=True, inplace=True)
#     df_eval.reset_index(drop=True, inplace=True)

#     return df_train, df_eval


# def create_histogram(data: pd.Series, bins: int, x_label: str, y_label: str, title: str, **kwargs) -> None:
#     """Generates a histogram from the provided DataFrame column (series) and displays it.

#     Title and labels are required, but if you want to add extra arguments for the histogram from the docs its easy to pass, see the example below.

#     Histogram docs for reference: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hist.html

#     Example:
#     ```
#     # Range isn't in the params of this function, but **kwargs lets us pass it to the histogram function.
#     helpers.create_histogram(my_df["my_column"], 10, range=(1, 2))
#     ```

#     Args:
#         data (pd.Series): Series (df column) with your data to plot.
#         bins (int): Number of bins to display data as.
#         x_label (str): X Axis Label.
#         y_label (str): Y Axis Label.
#         title (str): Title for chart.

#     """
    
#     plt.hist(data, bins=bins, edgecolor='black', **kwargs)
#     plt.title(title)
#     plt.ylabel(y_label)
#     plt.xlabel(x_label)

#     plt.show()


# def _get_ssm_parameter_value(parameter_name: str):

#     ssm_client = boto3.client("ssm")
#     client_reponse = ssm_client.get_parameter(Name=parameter_name)

#     return client_reponse["Parameter"]["Value"]


# def _client_uses_elbu_cluster(lkupclientid) -> bool:

#     return int(lkupclientid) in [96, 98, 99, 100]


# def get_cluster_endpoints():

#     ssm_param = ("/data-sci/redshift/cluster_endpoints")
#     cluster_endpoints = json.loads(_get_ssm_parameter_value(ssm_param))

#     return cluster_endpoints


# def get_cluster_name(lkupclientid: int) -> str:

#     ssm_param = ("/model/data-sci-product-propensity/redshift/cluster_environment") + '-app'

#     cluster_name = _get_ssm_parameter_value(ssm_param)

#     if _client_uses_elbu_cluster(lkupclientid):
#         cluster_name += "-elbu"

#     return cluster_name


# def assume_iam_role(role_arn: str):

#     sts_client = boto3.client("sts")

#     sts_response = sts_client.assume_role(
#         RoleArn=role_arn, RoleSessionName="ds_session",
#     )

#     session_id = sts_response["Credentials"]["AccessKeyId"]
#     session_key = sts_response["Credentials"]["SecretAccessKey"]
#     session_token = sts_response["Credentials"]["SessionToken"]

#     boto3.setup_default_session(
#         region_name="us-east-1",
#         aws_access_key_id=session_id,
#         aws_secret_access_key=session_key,
#         aws_session_token=session_token,
#     )