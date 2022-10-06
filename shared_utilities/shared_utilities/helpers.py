import botocore
import boto3
import json
import pandas as pd
import pyodbc
import psycopg2
import subprocess

from sqlalchemy import true


def hello_world():
    
    return "Hello World"

def get_aws_session(profile, retry = True):
    
    session = boto3.Session(profile_name=profile)
    sts = session.client('sts')
    
    try:
        identity = sts.get_caller_identity()
        print(f"Authorized as {identity['UserId']}")
        return session
    
    except botocore.exceptions.UnauthorizedSSOTokenError:
        if retry:
            subprocess.run(['aws','sso', 'login', '--profile', profile])
            return get_aws_session(profile, False)
    
        else:
            raise


def get_redshift_connection(cluster: str, database: str) -> psycopg2._psycopg.connection:
    
    session = get_aws_session("Stellaralgo-DataScienceAdmin")
    client = session.client('redshift')

    if cluster == 'qa-app':
        endpoint = 'qa-app.ctjussvyafp4.us-east-1.redshift.amazonaws.com'
    elif cluster == 'prod-app':
        endpoint = 'prod-app.ctjussvyafp4.us-east-1.redshift.amazonaws.com'
    elif cluster == 'qa-app-elbu':
        endpoint = 'qa-app-elbu.ctjussvyafp4.us-east-1.redshift.amazonaws.com'
    elif cluster == 'prod-app-elbu':
        endpoint = 'prod-app-elbu.ctjussvyafp4.us-east-1.redshift.amazonaws.com'

    cluster_credentials = client.get_cluster_credentials(
        ClusterIdentifier = cluster,
        DbUser = 'admin',
        DbName = database,
        DbGroups = ["admin_group"],
        AutoCreate = True
    )
    cnxn = psycopg2.connect(
        host = endpoint,
        port = 5439,
        user = cluster_credentials["DbUser"],
        password = cluster_credentials["DbPassword"],
        database = database
    )

    return cnxn


def get_retention_dataset(cluster:str, database:str, lkupclientid:str, start_year:int, end_year:int) -> pd.DataFrame:

    conn = get_redshift_connection(cluster, database)

    cur = conn.cursor()
    cur.execute(f"CALL ds.getretentionmodeldata({lkupclientid}, {start_year}, {end_year}, 'rkcursor')")

    named_cursor = conn.cursor('rkcursor')
    data = named_cursor.fetchall()

    cols = [row[0] for row in named_cursor.description]
    df = pd.DataFrame(data=data, columns=cols)

    conn.commit()

    return df


def get_product_propensity_dataset(cluster:str, database:str, lkupclientid:str, start_year:int, end_year:int) -> pd.DataFrame:

    conn = get_redshift_connection(cluster, database)

    cur = conn.cursor()
    cur.execute(f"CALL ds.getproductpropensitymodeldata({lkupclientid}, {start_year}, {end_year}, 'rkcursor')")

    named_cursor = conn.cursor('rkcursor')
    data = named_cursor.fetchall()

    cols = [row[0] for row in named_cursor.description]
    df = pd.DataFrame(data=data, columns=cols)

    conn.commit()

    return df


def get_event_propensity_training_dataset(cluster:str, database:str, lkupclientid:str, start_year:int, end_year:int) -> pd.DataFrame:

    conn = get_redshift_connection(cluster, database)

    cur = conn.cursor()
    cur.execute(f"CALL ds.geteventpropensitytrainingdata({lkupclientid}, {start_year}, {end_year}, 'rkcursor')")

    named_cursor = conn.cursor('rkcursor')
    data = named_cursor.fetchall()

    cols = [row[0] for row in named_cursor.description]
    df = pd.DataFrame(data=data, columns=cols)

    conn.commit()

    return df


def get_event_propensity_scoring_dataset(cluster:str, database:str, lkupclientid:str, game_date:str) -> pd.DataFrame:

    conn = get_redshift_connection(cluster, database)

    cur = conn.cursor()
    cur.execute(f"CALL ds.geteventpropensityscoringdata({lkupclientid}, cast('{game_date}' as date), 'rkcursor')")

    named_cursor = conn.cursor('rkcursor')
    data = named_cursor.fetchall()

    cols = [row[0] for row in named_cursor.description]
    df = pd.DataFrame(data=data, columns=cols)

    conn.commit()

    return df


def get_event_propensity_gamedays(cluster:str, database:str, lkupclientid:str) -> pd.DataFrame:

    conn = get_redshift_connection(cluster, database)

    cur = conn.cursor()
    cur.execute(f"""
        SELECT DISTINCT SPLIT_PART(eventdate, ' ', 1) as game_date
        FROM {database}.dw.cohortpurchase 
        WHERE lkupclientid = {lkupclientid}
        AND eventdate > CURRENT_DATE 
        AND productgrouping = 'Full Season'
        ORDER BY game_date
    """)

    data = cur.fetchall()

    cols = [row[0] for row in cur.description]
    df = pd.DataFrame(data=data, columns=cols)

    conn.commit()

    return df


