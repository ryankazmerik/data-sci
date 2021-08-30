import json
import pandas as pd
import pyodbc

SERVER = '52.44.171.130' 
DATABASE = 'datascience' 
USERNAME = 'nrad' 
PASSWORD = 'ThisIsQA123' 
CNXN = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+SERVER+';DATABASE='+DATABASE+';UID='+USERNAME+';PWD='+ PASSWORD)


def get_training_dataset(client_id, product, train_season_year):

    cursor = CNXN.cursor()

    querytrain =  f'''
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
    '''
    
    df_train = pd.read_sql(querytrain, CNXN)
    
    CNXN.commit()
    cursor.close()

    return df_train



if __name__ == "__main__":

    with open('../productyeartest.json') as teams_config:

        data = json.load(teams_config)
        
        # LOOP THROUGH ALL TEAMS 
        for team in data:
            
            client_id = team['lkupclientid']

            # LOOP THROUGH ALL PRODUCTS
            for product in team['products']:
                
                print(client_id, product['type'], product['train_year'])
                
                df_train = get_training_dataset(
                    client_id, 
                    product['type'], 
                    product['train_year']
                )

                print(df_train.info())