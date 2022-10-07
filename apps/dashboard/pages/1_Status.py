from datetime import datetime, timedelta, timezone
import botocore
import boto3
import io
import json
import pandas as pd
import streamlit as st
import subprocess
import tarfile

# from shared_utilities import helpers

pd.set_option('display.max_colwidth', None)

session = None

def establish_aws_session(profile, retry = True):
    
    session = boto3.Session(profile_name=profile)
    sts = session.client('sts')
    
    try:
        identity = sts.get_caller_identity()
        print(f"Authorized as {identity['UserId']}")
        return session
    
    except botocore.exceptions.UnauthorizedSSOTokenError:
        if retry:
            subprocess.run(['aws','sso', 'login', '--profile', profile])
            return establish_aws_session(profile, False)
    
        else:
            raise

# @st.cache(hash_funcs={"_thread.lock": lambda _: None, "ssl.SSLContext": lambda _: None, "_thread.RLock": lambda _: None})
def get_bucket_items(session, bucket, prefix):
    s3 = session.client('s3')
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    files = response["Contents"]

    while response["IsTruncated"] == True:
        response = s3.list_objects_v2(Bucket=bucket, ContinuationToken=response["NextContinuationToken"])
        files.extend(response["Contents"])
    
    return files

def get_curated_bucket_status(session, bucket, model):
    model_name_cleaned = model.lower().replace(' ', '-')
    prefix = f"{model_name_cleaned}-scores"
    files = get_bucket_items(session, bucket, prefix)

    modified_file_list = []
    for f in files:

        new_dict = {}
        split_key = f["Key"].split("/")

        if len(split_key) < 3:
            continue

        new_dict["Key"] = f["Key"]
        new_dict["Subtype"] = split_key[2]
        new_dict["Date"] = split_key[1].replace("date=", "")
        new_dict["LastModified"] = f["LastModified"]
        modified_file_list.append(new_dict)


    file_df = pd.DataFrame.from_records(modified_file_list)
    file_df = file_df.sort_values('LastModified')
    file_df = file_df[file_df["Key"].str.contains("scores.csv")]
    file_df = file_df.drop_duplicates('Subtype',keep='last')
    file_df = file_df.sort_values('Subtype').reset_index(drop=True)

    return file_df

def get_model_bucket_inference_status(session, env):
    pass


def create_curated_report(df):
    today = datetime.today()
    # df["days_since_last_run"] = df["Date"] - today #- pd.Timestamp.now().normalize()
    # df["days_since_last_run"] = df["LastModified"].apply(lambda x:  datetime.now() - x) #timedelta(datetime.strptime(x, "%Y-%m-%d").date()))
    # df["days_since_last_run"] = df["LastModified"].apply(lambda x: datetime(x, tzinfo=timezone.utc))
    df["Date"] = pd.to_datetime(df["Date"])
    df["test"] = pd.to_datetime(datetime.today()) - df["Date"]
    df["Curated_Bucket_Last_Success_Days"] = df["test"].astype(str).str.split(" ").str[0]
    df["Date"] = df["Date"].dt.strftime('%Y.%m.%d')
    df.drop(["test", "LastModified"], axis=1, inplace=True)
    #  - datetime.now(timezone.utc)
    # df["days_since_last_run"] = df["Date"].apply(lambda x: )
    return df


def get_s3_path(enviro, model_type, bucket_type):

    settings = {
        "Explore-US":{
            "Retention": {
                "model": "explore-us-model-data-sci-retention-us-east-1-ut8jag",
                "curated": "explore-us-curated-data-sci-retention-us-east-1-ut8jag"
            },
            "Product Propensity": {
                "model": "explore-us-model-data-sci-product-propensity-us-east-1-u8gldf",
                "curated": "explore-us-curated-data-sci-product-propensity-us-east-1-u8gldf"
            },
            "Event Propensity": {
                "model": "explore-us-model-data-sci-event-propensity-us-east-1-tykotu",
                "curated": ""
            }
        },
        "QA":{
            "Retention": {
                "model": "",
                "curated": "qa-curated-data-sci-retention-us-east-1-j58tuq"
            },
            "Product Propensity": {
                "model": "",
                "curated": "qa-curated-data-sci-product-propensity-us-east-1-mgwy8o"
            },
            "Event Propensity": {
                "model": "",
                "curated": ""
            }
        },
        "US":{
            "Retention": {
                "model": "",
                "curated": ""
            },
            "Product Propensity": {
                "model": "",
                "curated": "us-curated-data-sci-product-propensity-us-east-1-d2n55o"
            },
            "Event Propensity": {
                "model": "",
                "curated": ""
            }
        }
    }
    
    s3_bucket = settings[enviro][model_type][bucket_type]

    return s3_bucket


# ____________________________________ Streamlit ____________________________________

# SIDEBAR COMPONENTS
env_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}

env = st.sidebar.selectbox('Select Algorithm:', env_choices.keys(), format_func=lambda x:env_choices[x])
model_type = st.sidebar.radio('Model:',('Retention', 'Product Propensity', 'Event Propensity'))

session = establish_aws_session(env)

curated_bucket = get_s3_path(env_choices[env], model_type, "curated")

curated_df = get_curated_bucket_status(session, curated_bucket, model_type)

curated_df = create_curated_report(curated_df)

# st.dataframe(curated_df, width=5000)
df = curated_df.to_html(escape=False)
st.write(df, unsafe_allow_html=True)