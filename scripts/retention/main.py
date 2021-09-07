import json

import data
import train
import inference

if __name__ == "__main__":

    with open('../../productyeartest.json') as teams_config:

        dataset = json.load(teams_config)
        
        # LOOP THROUGH ALL TEAMS 
        for team in dataset:
            
            client_id = team['lkupclientid']

            # LOOP THROUGH ALL PRODUCTS
            for product in team['products']:
                                
                # GET FULL, TRAIN AND EVAL DATASETS
                df, df_train = data.get_dataset(
                    client_id, 
                    product['type'], 
                    product['train_year']
                )
                
                #TRAIN MODELS FOR EACH TEAM-PRODUCT
                model = [train.train_models(df_train)]

                




