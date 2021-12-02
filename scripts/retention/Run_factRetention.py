import psycopg2
import getpass
import pandas as pd
import pyodbc
import sys
import warnings

if not sys.warnoptions:
    warnings.simplefilter("ignore")


# override SSM server IP to public IP (for local testing)
CONN["server"] = "52.44.171.130"

def run_fact():

    CNXN = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server}"
        + ";SERVER="
        + CONN["server"]
        + ";DATABASE="
        + team["stlrDBName"]
        + ";UID="
        + CONN["username"]
        + ";PWD="
        + CONN["password"]
    )

    print(CONN)

    cursor = CNXN.cursor()
    storedProc = f"""Exec [DS].[Run_factCustomerRetention_Full_LOAD] """

    df = pd.read_sql(storedProc, CNXN)

    CNXN.commit()
    cursor.close()
    return df