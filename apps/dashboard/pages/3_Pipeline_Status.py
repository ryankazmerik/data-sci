import botocore
import boto3
import io
import json
import pandas as pd
import numpy as np
import re
import streamlit as st

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
    if model_name_cleaned == "retention":
        prefix = "date="
    else:
        prefix = f"{model_name_cleaned}-scores"
    files = helpers.get_s3_bucket_items(_session, bucket, prefix)

    modified_file_list = []
    for f in files:
        print(f)
        new_dict = {}
        split_key = f["Key"].split("/")

        if len(split_key) < 3:
            continue

        new_dict["Key"] = f["Key"]
        if model_name_cleaned == "retention":
            new_dict["Subtype"] = split_key[1]
            new_dict["Date"] = split_key[0].replace("date=", "")
        else:
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

def list_pipelines(_session, model):
    
    sm = _session.client("sagemaker")

    response = sm.list_pipelines(PipelineNamePrefix=f"data-sci-{model}", SortBy="Name", SortOrder="Ascending")
    pipelines = response["PipelineSummaries"]

    token = response.get("NextToken", False)
    try:
        while token:
            response = sm.list_pipelines(NextToken=response["NextToken"])
            pipelines.extend(response["PipelineSummaries"])
    except Exception as e:
        print(f"Getting next set with NextToken {token} failed.") 
    
    # This catches all of the old MLS-Galaxy pipelines before when a hash would follow MLS-Galaxy
    pipeline_format_invalid_regex = re.compile(r"MLS-Galaxy-\w+")
    
    final_pipeline_list = []
    for pipeline in pipelines:
        if not pipeline_format_invalid_regex.search(pipeline["PipelineName"]):
            final_pipeline_list.append(pipeline)
    
    return final_pipeline_list

@st.experimental_memo
def get_pipeline_status(_session, pipeline_name, pipeline_last_execution_time):
    
    # !!!!!!! The execution time is added as a param to cache results if no new executions have been ran to avoid rampant API calls. !!!!!!!
    sm = _session.client("sagemaker")

    response = sm.list_pipeline_executions(PipelineName=pipeline_name, MaxResults=1, SortOrder="Descending")
    result = response["PipelineExecutionSummaries"][0]

    return result


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


def create_side_by_side_df_view(df, hyperlink_col_name: str = None):
    cell_renderer =  JsCode("""
    function(params) {return `${params.value}`}
    """)

    missing_curated_style = JsCode(
    """
    function(params) {
        if (!params.value) {
            return {
                'color': 'white',
                'backgroundColor': 'darkred'
            }
        } 
    };
    """
    )

    greater_than_3_days_style = JsCode(
    """
    function(params) {
        if (params.value > 7) {
            return {
                'color': 'white',
                'backgroundColor': 'darkred'
            }
        } 
        else if (params.value > 3) {
            return {
                'color': 'black',
                'backgroundColor': 'orange'
            }
        }
    };
    """
    )

    diff_greater_than_0 = JsCode(
    """
    function(params) {
        if (params.value > 0) {
            return {
                'color': 'white',
                'backgroundColor': 'darkred'
            }
        } 
    };
    """
    )


    options_builder = GridOptionsBuilder.from_dataframe(df)
    
    if hyperlink_col_name:
        options_builder.configure_column(hyperlink_col_name, cellRenderer=cell_renderer) 
    options_builder.configure_column("Key_y", cellStyle=missing_curated_style)
    options_builder.configure_column("Prepipeline_Last_Success_Days", cellStyle=greater_than_3_days_style)
    options_builder.configure_column("Curated_Last_Success_Days", cellStyle=greater_than_3_days_style)
    options_builder.configure_column("pre_diff_curated_days", cellStyle=diff_greater_than_0)

    
    grid_options = options_builder.build()

    grid_return = AgGrid(df, grid_options, fit_columns_on_grid_load=True, allow_unsafe_jscode=True) 
    return grid_return


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

# MAIN COMPONENTS
st.title("Pipeline Status")

# SIDEBAR COMPONENTS
env_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}

env = st.sidebar.selectbox('Environment:', env_choices.keys(), format_func=lambda x:env_choices[x])
model_type = st.sidebar.radio('Model:',('Event Propensity', 'Product Propensity', 'Retention'), index=1)

session = helpers.establish_aws_session(env)

curated_bucket = get_s3_path(env_choices[env], model_type, "curated")
curated_df = get_curated_bucket_status(session, curated_bucket, model_type)
curated_df = create_curated_report(curated_df)

model_bucket = get_s3_path(env_choices[env], model_type, "model")
model_df = get_model_bucket_pre_pipeline_status(session, model_bucket, model_type)
model_df = create_model_report(model_df)



# ------ Create Joined DF (will be a function when done)
curated_df_modified_subtype = curated_df.copy()
curated_df_modified_subtype["Subtype"] = curated_df_modified_subtype["Subtype"].apply(lambda x: x.replace("nhl", "").replace("milb", "").replace("cfl", "").replace("mls", "").replace("nba", "").lower())
model_df = model_df[model_df["Subtype"].str.contains("-")]
model_df["split_subtype"] = model_df["Subtype"].apply(lambda x: x.split("-")[1].lower())
joined_df = model_df.merge(curated_df_modified_subtype, left_on="split_subtype", right_on="Subtype", how="left")

joined_df["Curated_Last_Success_Days"] = pd.to_numeric(joined_df.Curated_Last_Success_Days.astype(str).str.replace(',',''), errors='coerce')\
              .fillna(0)\
              .astype(int)

joined_df["Prepipeline_Last_Success_Days"] = pd.to_numeric(joined_df.Prepipeline_Last_Success_Days.astype(str).str.replace(',',''), errors='coerce')\
              .fillna(0)\
              .astype(int)
joined_df["pre_diff_curated_days"] = joined_df["Curated_Last_Success_Days"].sub(joined_df["Prepipeline_Last_Success_Days"], fill_value=0)
model_df.drop("split_subtype", axis=1, inplace=True)



# ------ Display Results
with st.expander("Overall Status", expanded=True):
    st.write("Below is a view of the prepipeline and curated status side-by-side. X is prepipeline and Y is curated.")
    st.write("The calculated columns that have the suffix `_Days` show how many days since the file has been updated.")
    st.write("`pre_diff_curated_days` shows the number of days between the prepipeline and curated files being updated. Meaning if its over 0, one hasn't run while the other did.")
    create_side_by_side_df_view(joined_df)

with st.expander("Preprocess Status"):
    st.write("A simple report of the last update time for each subtype and file size. This shows teh preprocess bucket/folder.")
    create_df_view(model_df)
    
with st.expander("Curated Status"):
    st.write("A simple report of the last update time for each subtype and file size. This shows the curated bucket (scores output)")
    create_df_view(curated_df)

with st.expander("Sagemaker Pipeline Runs"):
    pipelines = list_pipelines(session, model_type.replace(" ", "-").lower())
    # st.write(pipelines)

    for p in pipelines:
        st.markdown("""---""") 
        col1, col2, col3 = st.columns(3)

        status = get_pipeline_status(session, p["PipelineName"], p["LastModifiedTime"].strftime("%m/%d/%Y, %H:%M:%S"))

        with col1:
            st.write(p["PipelineName"])
        with col2:
            st.write(status["StartTime"])
        with col3:
            st.write(status["PipelineExecutionStatus"])
            if status["PipelineExecutionStatus"] == "Executing":
                st.markdown(":arrows_counterclockwise:")
            elif status["PipelineExecutionStatus"] == "Stopping":
                st.markdown(":soon: :stop_sign:")
            elif status["PipelineExecutionStatus"] == "Stopped":
                st.markdown(":stop_sign:")
            elif status["PipelineExecutionStatus"] == "Failed":
                st.markdown(":x:")
            elif status["PipelineExecutionStatus"] == "Succeeded":
                st.markdown(":white_check_mark:")    