import boto3
import json
import pandas as pd
import numpy as np
import re
import streamlit as st


from boto3.s3.transfer import TransferConfig
from datetime import datetime, timedelta, timezone
from data_sci_toolkit.aws_tools import lambda_tools
from shared_utilities import helpers
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid import JsCode
from urllib.parse import urlparse

pd.set_option('display.max_colwidth', None)
st.set_page_config(layout="wide")

session = None

@st.experimental_memo
def get_model_paths(_session, bucket, model):
    model_name_cleaned = model.lower().replace(' ', '-')
    prefix = f"training"
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
        modified_file_list.append(new_dict)


    file_df = pd.DataFrame.from_records(modified_file_list)
    file_df = file_df.sort_values('LastModified')
    file_df = file_df[file_df["Key"].str.contains(".tar.gz")]
    file_df = file_df.drop_duplicates('Subtype',keep='last')
    file_df = file_df.sort_values('Subtype').reset_index(drop=True)

    return file_df

def split_bucket(destination_env, s3_uri):
    s3_url_parsed = urlparse(s3_uri, allow_fragments=False)

    bucket_name = s3_url_parsed.netloc
    bucket_key  = s3_url_parsed.path

    bucket_array = bucket_name.split("-")
    product = re.search("product-propensity|retention|event-propensity", s3_uri).group()
    print(f"Product: {product}")
    region = "-".join(bucket_array[-4:-1])
    print(f"Region: {region}")

    key_array = bucket_key.split("/")
    print(f"Key Array: {key_array}")
    model_subtype = re.search("training/(\w+-\w+|\w+)", s3_uri).groups()[0]
    print(f"Model subtype: {model_subtype}")
    extracted_date = re.search("\d+-\d+-\d+", s3_uri).group()
    print(f"Extracted Date: {extracted_date}")
    training_id = re.search("\w+-\w+-TrainingStep-\w+", s3_uri).group()
    print(f"Training id: {training_id}")
    return (bucket_name, bucket_key, product, region, model_subtype, extracted_date, training_id)

    

def promote_team(key, bucket, model, role_name, destination_bucket_id, aws_config):

    destination_environment = aws_config["destination_environment"]
    aws_account_id = aws_config["aws_account_id"]
    aws_profile_name = aws_config["aws_profile_name"]
    aws_old_profile = aws_config["aws_current_profile"]
    subnets = aws_config["subnets"]
    sgs = aws_config["sgs"]

    temp_session = helpers.establish_aws_session(aws_profile_name)
    
    sagemaker_client = temp_session.client("sagemaker")
    ssm_client = temp_session.client("ssm")

    s3_uri = f"s3://{bucket}/{key}"
    random_bucket_id = bucket.split("-")[-1]
    print(f"Random bucket id: {random_bucket_id}")
    
    bucket_name, bucket_key, product, region, model_subtype, extracted_date, training_id = split_bucket(destination_environment, s3_uri)

    container_image = f"{aws_config['aws_account_id']}.dkr.ecr.us-east-1.amazonaws.com/data-sci-{model}-model:latest"
    date = str(datetime.now()).split(" ")[0]

    destination_bucket = f"{destination_environment}-model-data-sci-{model}-{region}-{destination_bucket_id}"
    destination_key = f"training/{model_subtype}/training-output/date={extracted_date}/{training_id}/output/model.tar.gz"

    print(f"From Bucket: {bucket_name}")
    print(f"From key: {bucket_key}")
    
    print(f"Destination bucket: {destination_bucket}")
    print(f"Destination key: {destination_key}")

    
    try:

        # old_env_session = boto3.setup_default_session(profile_name=aws_old_profile)
        old_env_session = helpers.establish_aws_session(aws_old_profile)
        

        old_s3 = old_env_session.client("s3")

        # files = old_s3.list_objects_v2(Bucket=bucket_name, Prefix="training/")
        # print(f"Files: {files}")
        try:
            old_s3.download_file(bucket_name, bucket_key[1:], "data/model.tar.gz")
        except Exception as e:
            print(f"Failed to download file w/ exception: {e}")
        
        new_s3 = temp_session.client("s3")
        try:
            new_s3.upload_file("data/model.tar.gz", destination_bucket, destination_key)
        except Exception as e:
            print(f"Failed to upload file w/ exception: {e}")

        full_model_name = f"data-sci-{model}-{model_subtype}-{date}"

        response = sagemaker_client.create_model(
            ModelName=full_model_name,
            PrimaryContainer={
                "Image": container_image,
                "ImageConfig": {
                    "RepositoryAccessMode": "Platform"
                },
                "Mode": "SingleModel",
                "ModelDataUrl": f"s3://{destination_bucket}/{destination_key}",
                # "ModelPackageName": "arn:aws:sagemaker:us-east-1:564285676170:model-package/model-retention-milb"
                # "ModelPackageName": f"arn:aws:sagemaker:{region}:{aws_account_id}:model-package-group/data-sci-{product}-{model_name}-{training_id}",
            },

            ExecutionRoleArn=f"arn:aws:iam::{aws_account_id}:role/{role_name}",
            Tags=[
                {
                    "Key": "model",
                    "Value": model
                },
                {
                    "Key": "model_subtype",
                    "Value": model_subtype
                },
                {
                    "Key": "environment",
                    "Value": destination_environment
                },
                {
                    "Key": "region",
                    "Value": region
                },
                {
                    "Key": "training_id",
                    "Value": training_id
                },
                {
                    "Key": "date",
                    "Value": date
                }
            ],
            VpcConfig={
                "SecurityGroupIds": sgs,
                "Subnets": subnets
            },
            EnableNetworkIsolation=True
        )

        print(response)

    except Exception as e:
        print("ERROR: Could not create sagemaker model.")
        print(e)

    # Register Model


    # Update SSM Parameter
    
    
    ssm_parameter_path = f"/model/data-sci-{product}/deployed_model_names"

    try:
        ssm_parameter = ssm_client.get_parameter(
            Name=ssm_parameter_path,
            WithDecryption=True
        )

        print(ssm_parameter)

    except Exception as e:
        print("ERROR: Parameter was not successfully retrieved.")
        print(e)

    ssm_payload = json.loads(ssm_parameter["Parameter"]["Value"]) 

    if model == "product-propensity":
        ssm_payload[model_subtype] = f"{model_subtype}-{date}"
    else:
        ssm_payload[model_subtype] = full_model_name

    try:
        response = ssm_client.put_parameter(
            Name=ssm_parameter_path,
            Value=json.dumps(ssm_payload),
            Type="String",
            Overwrite=True
        )

        print(response)
    except Exception as e:
        print("ERROR: Parameter was not successfully updated.")
        print(e)



def create_curated_report(df):

    df["Date"] = pd.to_datetime(df["Date"])
    df["date_diff"] = pd.to_datetime(datetime.today()) - df["Date"]
    df["Curated_Last_Success_Days"] = df["date_diff"].astype(str).str.split(" ").str[0]
    df["Date"] = df["Date"].dt.strftime('%Y.%m.%d')
    df.drop(["date_diff", "LastModified"], axis=1, inplace=True)

    return df



def get_aws_configuration(enviro):

    settings = json.load(open("./settings.json"))
    aws_configuration = settings[enviro]

    return aws_configuration


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
st.title("Model Promotion")

# SIDEBAR COMPONENTS
env_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}

env = st.sidebar.selectbox('Environment:', env_choices.keys(), format_func=lambda x:env_choices[x])
model_type = st.sidebar.radio('Model:',('Event Propensity', 'Product Propensity', 'Retention'), index=1)

session = helpers.establish_aws_session(env)

aws_config = get_aws_configuration(env_choices[env])
model_bucket = aws_config[model_type]["model"]
role_name = aws_config[model_type]["role_name"]
destination_bucket_id = aws_config[model_type]["destination_bucket_id"]
file_df = get_model_paths(session, model_bucket, model_type)

files = file_df.to_records()

st.write("You can train, promote up to QA and PROD environments, and run inference on your models here:")

team_uris_to_promote = []
col1, col2, col3, col4, col5 = st.columns(5)
col1.write("### Model Subtype")
col2.write("### Last Updated Date")
col3.write("### Run Train Script")
col4.write("### Run Promote Script")
col5.write("### Run Inference Script")

for f in files:
    st.markdown("""---""") 
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.write(f"{f[2]}")
    with col2:
        st.write(f"{f[3]}")
    with col3:
        if env == "Explore-US-DataScienceAdmin":
            train = (st.button(f"Train: {f[2]}",key=f"train-{f[2]}")) 
            if train:
                with st.spinner(text=f"Launching Training Lambda {f[2]}"):
                    lambda_tools.kickoff_ml_pipeline(session, "-".join(model_type.lower().split(" ")), f[2], "training")
                st.success(f"Finished launching train Lambda {f[2]}")
    with col4:
        if env != "US-StellarSupport":
            promote = (st.button(f"Promote: {f[2]}",key=f"promote-{f[2]}")) 
            if promote:
                with st.spinner(text=f"Promoting {f[2]}"):
                    team_uris_to_promote.append(f"s3://{model_bucket}/{f[1]}")
                    promote_team(f[1], model_bucket, model_type.replace(" ", "-").lower(), role_name, destination_bucket_id, aws_config)
                st.success(f"Finished promoting {f[2]}")
    with col5:
        inference = (st.button(f"Inference: {f[2]}",key=f"inference-{f[2]}")) 
        if inference:
            with st.spinner(text=f"Launching Inference Lambda {f[2]}"):
                lambda_tools.kickoff_ml_pipeline(session, "-".join(model_type.lower().split(" ")), f[2], "inference")
            st.success(f"Finished launching inference Lambda {f[2]}")
            
st.write(team_uris_to_promote)

with open('./style.css') as css: st.markdown(css.read(), unsafe_allow_html=True)