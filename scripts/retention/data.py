import pandas as pd
import pyodbc

SERVER = '52.44.171.130' 
DATABASE = 'datascience' 
USERNAME = 'nrad' 
PASSWORD = 'ThisIsQA123' 
CNXN = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+SERVER+';DATABASE='+DATABASE+';UID='+USERNAME+';PWD='+ PASSWORD)


def get_dataset(client_id, product, train_season_year):

    cursor = CNXN.cursor()

    query =  f"""
        SELECT 
            r.dimcustomermasterid,
            attendancePercent,
            distToVenue,
            isnextyear_buyer,
            missed_games_1,
            missed_games_2,
            missed_games_over_2,
            recency,
            renewedBeforeDays,
            source_tenure,
            totalSpent
        FROM 
            ds.retentionscoring r 
        WHERE 
            lkupclientid = {client_id} 
        AND 
            productgrouping = {"'"+ str(product) + "'"} 
        AND 
            year < {train_season_year};
    """
    
    df = pd.read_sql(query, CNXN)

    # CREATE THE TRAIN AND EVAL DATASETS
    df_train = df.sample(frac=0.95, random_state=786)

    # DROP dim_customer_master_id from train & eval datasets
    df_train.drop('dimcustomermasterid', axis=1, inplace=True)
    
    CNXN.commit()
    cursor.close()

    return df, df_train