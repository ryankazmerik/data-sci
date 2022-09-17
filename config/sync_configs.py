import boto3
import json
import pandas as pd

session = boto3.setup_default_session(profile_name='Stellaralgo-DataScienceAdmin')

def get_subtype_config_files():

    s3 = boto3.client('s3')

    # crawl pipelines folder for retention files
    my_bucket = s3.list_objects_v2(Bucket='ai-experimentation-td4np7', Prefix='pipelines')
    print(f'Peter Bucket/Folder/etc: {my_bucket}')
    print(f'\nObjects inside above: {[x for x in my_bucket["Contents"]]}')



if __name__ == "__main__":
    
    get_subtype_config_files()

