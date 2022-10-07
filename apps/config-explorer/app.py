import botocore
import boto3
import io
import json
import pandas as pd
import streamlit as st
import subprocess
import tarfile


st.set_page_config(page_icon="hockey", layout="wide")
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

#@st.cache()
def get_model_metadata_files(session, bucket):

    s3 = session.client('s3')
    response = s3.list_objects_v2(Bucket=bucket, Prefix='training')

    files = response["Contents"]

    while response["IsTruncated"] == True:
        response = s3.list_objects_v2(Bucket=bucket, ContinuationToken=response["NextContinuationToken"])
        files.extend(response["Contents"])

    # Filter to remove duplicates and get most recent date for each subtype
    modified_file_list = [{"Key": f["Key"], "Subtype": f["Key"].split("/")[1], "LastModified": f["LastModified"]} for f in files]
    file_df = pd.DataFrame.from_records(modified_file_list)
    file_df = file_df.sort_values('LastModified')
    file_df = file_df[file_df["Key"].str.contains(".tar.gz")]
    file_df = file_df.drop_duplicates('Subtype',keep='last')
    file_df = file_df.sort_values('Subtype')
    files = file_df.to_dict("records")
    
    # build a list of model metadata json files
    model_metadata_list = []
    for file in files:
            
        if file["Key"].endswith(".tar.gz"):

            model_file = s3.get_object(Bucket=bucket, Key=file["Key"])
            tar_content = model_file["Body"].read()

            # untar the model.tar.gz file
            with tarfile.open(fileobj=io.BytesIO(tar_content), mode="r:gz") as tar:

                for member in tar.getmembers():
                    
                    # grab the model metadata file
                    if member.name == "metadata.json":
                        model_metadata = json.load(tar.extractfile(member))
                        model_metadata["s3_path"] = f"{bucket}/{file['Key']}"
                        model_metadata["modified"] = file["LastModified"]
                        model_metadata_list.append(model_metadata)

    return model_metadata_list


def parse_config_files_into_df(config_files):

    df_list = []
    for file in config_files:  

        df = pd.DataFrame()
        df["model_subtype"] = [file["model_subtype"]]
        df["clientcode"] = [file["client_configs"][0]["clientcode"]]
        df["dbname"] = [file["client_configs"][0]["dbname"]]
        df["lkupclientid"] = [file["client_configs"][0]["lkupclientid"]]
        df["final_training_year"] = [file["client_configs"][0]["year"]]
        df["algorithms"] = [file["algorithm"]]
        df["s3_path"] = [file["s3_path"]]
        df["modified"] = [file["modified"]]
        #df["feature_importances"] = [file["feature_importances"]]

        df_list.append(df)

    df_all = pd.concat(df_list)

    df_all['s3_path'] = df_all['s3_path'].apply(make_clickable)

    df_all = df_all.reset_index(drop=True)

    return df_all



def get_s3_path(enviro, model_type):

    settings = {
        "Explore-US":{
            "Retention": "explore-us-model-data-sci-retention-us-east-1-ut8jag",
            "Product Propensity": "explore-us-model-data-sci-product-propensity-us-east-1-u8gldf",
            "Event Propensity": "explore-us-model-data-sci-event-propensity-us-east-1-tykotu"
        },
        "QA":{
            "Retention": "qa-model-data-sci-retention-us-east-1-j58tuq",
            "Product Propensity": "",
            "Event Propensity": "qa-model-data-sci-product-propensity-us-east-1-mgwy8o"
        },
        "US":{
            "Retention": "us-model-data-sci-retention-us-east-1-5h6cml",
            "Product Propensity": "us-model-data-sci-product-propensity-us-east-1-d2n55o",
            "Event Propensity": ""
        }
    }
    
    s3_bucket = settings[enviro][model_type]

    return s3_bucket


def make_clickable(link):

    aws_path = "https://s3.console.aws.amazon.com/s3/buckets/"
    return f'<a target="_blank" href="{aws_path}{link}">Click to Open</a>'


# SIDEBAR COMPONENTS
enviro_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}
enviro = st.sidebar.selectbox('Select Algorithm:', enviro_choices.keys(), format_func=lambda x:enviro_choices[x])

model_type = st.sidebar.radio('Model:',('Retention', 'Product Propensity', 'Event Propensity'))

# SECTION CONFIGURATION
section_1 = st.expander("Team Configuration", expanded=True)


# SECTION 1 : CONFIG DATASET
with section_1:

    # get session and s3 path for selected environment
    session = establish_aws_session(enviro)

    s3_bucket = get_s3_path(enviro_choices[enviro], model_type)

    # get a list of models and their metadata
    model_metadata_list = get_model_metadata_files(session, s3_bucket)
    
    # combine models list into a dataframe
    df = parse_config_files_into_df(model_metadata_list)

    # link is the column with hyperlinks

    #df = df.to_html(escape=False)
    #st.write(df, unsafe_allow_html=True)

    st._legacy_dataframe(df, 5000, 5000)
