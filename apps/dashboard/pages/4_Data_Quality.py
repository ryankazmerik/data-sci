import botocore
import boto3
import io
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import seaborn as sns
import streamlit as st

from datetime import datetime, timedelta, timezone
from shared_utilities import helpers
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid import JsCode

pd.set_option('display.max_colwidth', None)
st.set_page_config(layout="wide")

session = None

@st.experimental_memo
def get_inference_bucket_items(_session, bucket, model):
    prefix = f"inference"
    files = helpers.get_s3_bucket_items(_session, bucket, prefix)

    modified_file_list = []
    for f in files:

        new_dict = {}
        split_key = f["Key"].split("/")

        if len(split_key) < 3:
            continue

        new_dict["Key"] = f["Key"]
        new_dict["Subtype"] = split_key[1]
        new_dict["Date"] = split_key[3].replace("date=", "")
        new_dict["LastModified"] = f["LastModified"]
        new_dict["Size"] = f["Size"]
        modified_file_list.append(new_dict)


    file_df = pd.DataFrame.from_records(modified_file_list)
    file_df = file_df.sort_values('LastModified')
    file_df = file_df[file_df["Key"].str.contains(".csv.out")]
    file_df = file_df.drop_duplicates('Subtype',keep='last')
    file_df = file_df.sort_values('Subtype').reset_index(drop=True)

    return file_df

@st.experimental_singleton(suppress_st_warning=True)
def read_scores(_session, _file_df, team, bucket):
    st.write(f"Cache miss: read_scores ran: {team} - {bucket}")
    df = _file_df[_file_df["Subtype"] == team]
    files = df.to_dict("records")
    # scores = files
    s3 = _session.client("s3")
    csv_file = s3.get_object(Bucket=bucket, Key=files[0]["Key"])
    scores = pd.read_json(csv_file["Body"], lines=True)

    return scores


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
                "model": "explore-us-model-data-sci-event-propensity-us-east-1-yvf53s",
                "curated": "explore-us-curated-data-sci-event-propensity-us-east-1-yvf53s"
            }
        },
        "QA":{
            "Retention": {
                "model": "qa-model-data-sci-retention-us-east-1-j58tuq",
                "curated": "qa-curated-data-sci-retention-us-east-1-j58tuq"
            },
            "Product Propensity": {
                "model": "qa-model-data-sci-product-propensity-us-east-1-mgwy8o",
                "curated": "qa-curated-data-sci-product-propensity-us-east-1-mgwy8o"
            },
            "Event Propensity": {
                "model": "",
                "curated": ""
            }
        },
        "US":{
            "Retention": {
                "model": "us-model-data-sci-retention-us-east-1-5h6cml",
                "curated": "us-curated-data-sci-retention-us-east-1-5h6cml"
            },
            "Product Propensity": {
                "model": "us-model-data-sci-product-propensity-us-east-1-d2n55o",
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

if model_type == "Event Propensity":
    st.warning("Event Propensity has very large files, it may freeze your computer and cost losts on S3 if ran many times. It may not even work.")

session = helpers.establish_aws_session(env)

inference_bucket = get_s3_path(env_choices[env], model_type, "model")

file_df = get_inference_bucket_items(session, inference_bucket, model_type)

with st.expander("SAScore Distribution"):
    st.write("A report of the score distribution for the selected subtype.")
    selected_team = st.selectbox(
        "Select Team to View Data Quality", file_df["Subtype"].to_list()
    )

    selected_team_scores = read_scores(session, file_df, selected_team, inference_bucket).copy()
    fig1 = plt.figure(figsize=(6,3))
    sns.histplot(data=selected_team_scores, x='sascore', bins= 20, kde=True)    
    plt.title(selected_team, fontsize = 12)
    st.pyplot(fig1)

    if model_type != "Event Propensity":
        fig2 = plt.figure(figsize=(6,3))
        sns.histplot(data=selected_team_scores, x='sascore', hue='product', bins= 20, kde=True)    
        plt.title(selected_team, fontsize = 12)
        st.pyplot(fig2)


