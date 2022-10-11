import botocore
import boto3
import io
import json
import pandas as pd
import streamlit as st
import subprocess
import tarfile

from datetime import datetime, timedelta, timezone
from shared_utilities import helpers
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid import JsCode

pd.set_option('display.max_colwidth', None)
st.set_page_config(layout="wide")

session = None

@st.experimental_memo
def get_curated_bucket_status(_session, bucket, model):
    model_name_cleaned = model.lower().replace(' ', '-')
    prefix = f"{model_name_cleaned}-scores"
    files = helpers.get_s3_bucket_items(_session, bucket, prefix)

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
        new_dict["Size"] = f["Size"]
        modified_file_list.append(new_dict)


    file_df = pd.DataFrame.from_records(modified_file_list)
    file_df = file_df.sort_values('LastModified')
    file_df = file_df[file_df["Key"].str.contains("scores.csv")]
    file_df = file_df.drop_duplicates('Subtype',keep='last')
    file_df = file_df.sort_values('Subtype').reset_index(drop=True)

    return file_df

@st.experimental_memo
def get_model_bucket_pre_pipeline_status(_session, bucket, model):
    model_name_cleaned = model.lower().replace(' ', '-')
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
    file_df = file_df[file_df["Key"].str.contains(".parquet")]
    file_df = file_df.drop_duplicates('Subtype',keep='last')
    file_df = file_df.sort_values('Subtype').reset_index(drop=True)

    return file_df


def create_curated_report(df):

    df["Date"] = pd.to_datetime(df["Date"])
    df["date_diff"] = pd.to_datetime(datetime.today()) - df["Date"]
    df["Curated_Last_Success_Days"] = df["date_diff"].astype(str).str.split(" ").str[0]
    df["Date"] = df["Date"].dt.strftime('%Y.%m.%d')
    df.drop(["date_diff", "LastModified"], axis=1, inplace=True)

    return df

def create_model_report(df):

    df["Date"] = pd.to_datetime(df["Date"])
    df["date_diff"] = pd.to_datetime(datetime.today()) - df["Date"]
    df["Prepipeline_Last_Success_Days"] = df["date_diff"].astype(str).str.split(" ").str[0]
    df["Date"] = df["Date"].dt.strftime('%Y.%m.%d')
    df.drop(["date_diff", "LastModified"], axis=1, inplace=True)

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
                "curated": "explore-us-curated-data-sci-event-propensity-us-east-1-tykotu"
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
                "model": "",
                "curated": ""
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


def create_df_view(df, hyperlink_col_name: str = None):
    cell_renderer =  JsCode("""
    function(params) {return `${params.value}`}
    """)

    options_builder = GridOptionsBuilder.from_dataframe(df)
    
    if hyperlink_col_name:
        options_builder.configure_column(hyperlink_col_name, cellRenderer=cell_renderer) 
    
    grid_options = options_builder.build()

    grid_return = AgGrid(df, grid_options, fit_columns_on_grid_load=True, allow_unsafe_jscode=True) 
    return grid_return
    


# ____________________________________ Streamlit ____________________________________

# SIDEBAR COMPONENTS
env_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}

env = st.sidebar.selectbox('Select Algorithm:', env_choices.keys(), format_func=lambda x:env_choices[x])
model_type = st.sidebar.radio('Model:',('Retention', 'Product Propensity', 'Event Propensity'))

session = helpers.establish_aws_session(env)

curated_bucket = get_s3_path(env_choices[env], model_type, "curated")
curated_df = get_curated_bucket_status(session, curated_bucket, model_type)
curated_df = create_curated_report(curated_df)

model_bucket = get_s3_path(env_choices[env], model_type, "model")
model_df = get_model_bucket_pre_pipeline_status(session, model_bucket, model_type)
model_df = create_model_report(model_df)

model_df = model_df[model_df["Subtype"].str.contains("-")]
model_df["split_subtype"] = model_df["Subtype"].apply(lambda x: x.split("-")[1].lower())
joined_df = model_df.merge(curated_df, left_on="split_subtype", right_on="Subtype")

model_df.drop("split_subtype", axis=1, inplace=True)
# st.dataframe(curated_df, width=5000)
# df = curated_df.to_html(escape=False)
# st.write(df, unsafe_allow_html=True)

with st.expander("Overall Status"):
    create_df_view(joined_df)

with st.expander("Curated Status"):
    create_df_view(curated_df)

with st.expander("Preprocess Status"):
    create_df_view(model_df)