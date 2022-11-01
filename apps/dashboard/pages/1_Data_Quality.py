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

@st.experimental_memo
def get_curated_bucket_items(_session, bucket, model):
    model_name_cleaned = model.lower().replace(' ', '-')
    if model_name_cleaned == "retention":
        prefix = "date="
    else:
        prefix = f"{model_name_cleaned}-scores"
    files = helpers.get_s3_bucket_items(_session, bucket, prefix)

    modified_file_list = []
    for f in files:
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

@st.experimental_singleton(suppress_st_warning=True)
def read_scores(_session, _file_df, team, bucket, file_ext):

    st.write(f"Cache miss: read_scores ran: {team} - {bucket}")
    print(f"------ File ext: {file_ext} ------")


    alt_client_code = "NA"
    renamed_team = "NA"
    try:
        renamed_team = team.split("-")[1].lower()
        if team.lower() == "milb-66ers":
            alt_client_code = "milb-ie66"
        elif team.lower() == "milb-blazers":
            alt_client_code = "milb-ptb"
        elif team.lower() == "milb-hartfordyardgoats":
            alt_client_code = "milb-yardgoats"
    except:
        print("No alt code or renamed team applicable")
        

    df = _file_df[(_file_df["Subtype"] == team) | (_file_df["Subtype"] == "".join(team.split("-")).lower()) | (_file_df["Subtype"] == renamed_team) | (_file_df["Subtype"] == alt_client_code)]
    print(f"team: {team} | renamed team: {team} | subtype: {_file_df['Subtype'].to_list()} | split: {''.join(team.split('-')).lower()}")
    print(f"team: {team} | renamed team: {team} | subtype: {df['Subtype'].to_list()} | split: {''.join(team.split('-')).lower()}")
    files = df.to_dict("records")
    s3 = _session.client("s3")
    csv_file = s3.get_object(Bucket=bucket, Key=files[0]["Key"])
    
    if file_ext == ".csv.out":
        scores = pd.read_json(csv_file["Body"], lines=True)
    elif file_ext == ".csv":
        scores = pd.read_csv(io.StringIO(csv_file["Body"].read().decode("utf-8")))
        st.write(len(scores.index))

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


def show_product_propesnity_report():
    with st.expander("product_last & product_current by sascore & hue product"):
        st.write("Report showing distribution of product_last and product current for each prediction.")

        # temp_df = selected_team_scores["product"]
        for t in selected_team_scores["product"].unique():
            st.write(f"## Summary for product prediction is: `{t}`")
            col1, col2, col3 = st.columns(3)
            temp_df = selected_team_scores[selected_team_scores["product"] == t]
            # values = temp_df["product"].value_counts()
            col1.write("Value Summary for `product_current`")
            col1.write(temp_df["product_current"].value_counts())

            non_packages = ["None", "Individual", "Group", "Groups"]
            with col2:
                st.write(f"Chart with {', '.join(non_packages)}")
                fig = plt.figure(figsize=(6,3))
                sns.histplot(data=selected_team_scores[selected_team_scores["product"]==t], x='sascore', hue='product_current', bins=20, kde=True)
                plt.title(f"{selected_team} - {t} by product_current")
                st.pyplot(fig)
            
            with col3:
                st.write(f"Chart without {', '.join(non_packages)}")
                fig = plt.figure(figsize=(6,3))
                sns.histplot(data=selected_team_scores[(selected_team_scores["product"]==t) & (~selected_team_scores["product_current"].isin(non_packages))], x='sascore', hue='product_current', bins=20, kde=True)
                plt.title(f"{selected_team} - {t} by product_current")
                st.pyplot(fig)
            
            st.markdown("---")
        

        selected_product = st.selectbox("Select product", selected_team_scores["product"].unique())

        fig = plt.figure(figsize=(6,3))
        sns.histplot(data=selected_team_scores[selected_team_scores["product"]==selected_product], x='sascore', hue='product_current', bins=20, kde=True)
        plt.title(f"{selected_team} - {selected_product} by product_current")
        st.pyplot(fig)

def show_model_report(model):
    if model == "Product Propensity":
        show_product_propesnity_report()


# ____________________________________ Streamlit ____________________________________

# MAIN COMPONENTS
st.title("Data Quality")

# SIDEBAR COMPONENTS
env_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}

env = st.sidebar.selectbox('Environment:', env_choices.keys(), format_func=lambda x:env_choices[x])
model_type = st.sidebar.radio('Model:',('Event Propensity', 'Product Propensity', 'Retention'), index=1)

if model_type == "Event Propensity":
    st.warning("Event Propensity has very large files, it may freeze your computer and cost losts on S3 if ran many times. It may not even work.")

session = helpers.establish_aws_session(env)

inference_bucket = get_s3_path(env_choices[env], model_type, "model")
file_df = get_inference_bucket_items(session, inference_bucket, model_type)


selected_team = st.selectbox(
    "Select Team:", file_df["Subtype"].to_list()
)


selected_team_scores = read_scores(session, file_df, selected_team, inference_bucket, ".csv.out").copy()

if len(selected_team_scores.index) == 0:
    st.error("Empty Dataframe")

with st.expander("scores.csv Summary (after post pipeline)"):
    st.write("Report of scores in scores.csv")
    selected_head_count = st.number_input("Select number of rows to show from scores.csv", 5, 10000, step=1)
    curated_bucket = get_s3_path(env_choices[env], model_type, "curated")
    curated_df = get_curated_bucket_items(session, curated_bucket, model_type)
    selected_team_curated_scores = read_scores(session, curated_df, selected_team, curated_bucket, ".csv").copy()

    if len(selected_team_curated_scores.index) == 0:
        st.error("Empty Dataframe")

    st.write(selected_team_curated_scores.head(int(selected_head_count)))

    st.markdown("---")

    col1, col2 = st.columns(2)
    col1.write("Scores grouped by product")
    col2.write("Scores grouped by product & product_current")
    col1.write(selected_team_curated_scores.groupby(["product"]).agg(count=("product", "count")).reset_index(["product"]))
    
    if model_type not in ("Event Propensity", "Retention"):
        col2.write(selected_team_curated_scores.groupby(["product", "product_current"]).agg(count=("product", "count")).reset_index(["product", "product_current"]))

    st.markdown("---")

    st.write("A report of the score distribution for the selected subtype.")
    fig1 = plt.figure(figsize=(6,3))
    sns.countplot(data=selected_team_curated_scores[selected_team_curated_scores["product"] != "Any"], x='product')
    plt.title(selected_team, fontsize = 12)
    st.pyplot(fig1)

    if model_type not in ("Event Propensity", "Retention"):
        fig2 = plt.figure(figsize=(6,3))
        sns.countplot(data=selected_team_curated_scores[selected_team_curated_scores["product"] != "Any"], x='product', hue='product_current')
        plt.title(selected_team, fontsize = 12)
        st.pyplot(fig2)




show_model_report(model_type)




with st.expander("inference.csv.out Summary / SAScore Distribution (before post pipeline)"):
    st.write("A report of the score distribution for the selected subtype.")
    fig1 = plt.figure(figsize=(6,3))
    sns.histplot(data=selected_team_scores, x='sascore', bins= 20, kde=True)    
    plt.title(selected_team, fontsize = 12)
    st.pyplot(fig1)

    if model_type != "Event Propensity":
        fig2 = plt.figure(figsize=(6,3))
        sns.histplot(data=selected_team_scores, x='sascore', hue='product', bins= 20, kde=True)    
        plt.title(selected_team, fontsize = 12)
        st.pyplot(fig2)

