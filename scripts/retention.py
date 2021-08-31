import json
import pandas as pd
import pyodbc

from pycaret.classification import *

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
            recency,
            attendancePercent,
            totalSpent,
            distToVenue,
            source_tenure,
            renewedBeforeDays,
            missed_games_1,
            missed_games_2,
            missed_games_over_2,
            isnextyear_buyer
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
    
    df_train = df.sample(frac=0.95, random_state=786)
    df_eval = df.drop(df_train.index)

    df_train.reset_index(inplace=True, drop=True)
    df_eval.reset_index(inplace=True, drop=True)

    CNXN.commit()
    cursor.close()

    return df_train, df_eval


def train_models(df_train):

    model = setup(df_train, target='isnextyear_buyer', train_size = 0.8)

    lgbm = create_model('lightgbm')

    return lgbm

if __name__ == "__main__":

    with open('../productyeartest.json') as teams_config:

        data = json.load(teams_config)
        
        # LOOP THROUGH ALL TEAMS 
        for team in data:
            
            client_id = team['lkupclientid']

            # LOOP THROUGH ALL PRODUCTS
            for product in team['products']:
                
                print(client_id, product['type'], product['train_year'])
                
                # GET TRAIN AND EVAL DATASETS
                df_train, df_eval = get_dataset(
                    client_id, 
                    product['type'], 
                    product['train_year']
                )

                #TRAIN MODELS FOR EACH TEAM-PRODUCT
                train_models(df_train)



