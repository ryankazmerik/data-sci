import io
import json
import pandas as pd
import streamlit as st
import tarfile

from shared_utilities import helpers
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid import JsCode

pd.set_option('display.max_colwidth', None)
st.set_page_config(layout="wide")

session = None

@st.experimental_memo
def get_metadata_info(_session, bucket, model):
    files = helpers.get_s3_bucket_items(_session, bucket, "training")

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
    file_df = file_df[file_df["Key"].str.contains("tar.gz")]
    file_df = file_df.drop_duplicates('Subtype',keep='last')
    file_df = file_df.sort_values('Subtype').reset_index(drop=True)

    files = file_df.to_dict("records")

    model_metadata_list = []
    for file in files:
            
        if file["Key"].endswith(".tar.gz"):

            s3 = _session.client("s3")
            model_file = s3.get_object(Bucket=bucket, Key=file["Key"])
            tar_content = model_file["Body"].read()

            # untar the model.tar.gz file
            with tarfile.open(fileobj=io.BytesIO(tar_content), mode="r:gz") as tar:

                for member in tar.getmembers():
                    
                    # grab the model metadata file
                    if member.name == "metadata.json":
                        model_metadata = json.load(tar.extractfile(member))
                        model_metadata_list.append(model_metadata)

    return model_metadata_list


def get_model_bucket_inference_status(session, env):
    pass


def create_curated_report(config_files):

    df_list = []
    for idx, file in enumerate(config_files):  

        df = pd.DataFrame()
        df["no."] = [idx+1]
        df["lkupclientid"] = [file["client_configs"][0]["lkupclientid"]]
        df["model_subtype"] = [file["model_subtype"]]
        df["clientcode"] = [file["client_configs"][0]["clientcode"]]
        df["league"] = [file["model_subtype"].split("-")[0]]
        #df["cluster"] = [file["client_configs"][0]["cluster"]]
        df["dbname"] = [file["client_configs"][0]["dbname"]]
        df["final_training_year"] = [file["client_configs"][0]["year"]]
        df["algorithms"] = [file["algorithm"]]
        df["features"] = [file["feature_importances"]]
        
        df_list.append(df)

    df_all = pd.concat(df_list)

    df_all.columns = ["No.", "LkupClientId", "Model Subtype", "Client Code", "League", "RedShift Database", "Training Year", "Algorithm", "Features"]

    return df_all


def get_s3_path(enviro, model_type, bucket_type):

    settings = json.load(open("./settings.json"))
    s3_bucket = settings[enviro][model_type][bucket_type]

    return s3_bucket


# ____________________________________ Streamlit ____________________________________

# MAIN COMPONENTS
st.title("Team Configuration")

# SIDEBAR COMPONENTS
env_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}

env = st.sidebar.selectbox('Environment:', env_choices.keys(), format_func=lambda x:env_choices[x])
model_type = st.sidebar.radio('Model:',('Event Propensity', 'Product Propensity', 'Retention'), index=1)

session = helpers.establish_aws_session(env)

curated_bucket = get_s3_path(env_choices[env], model_type, "model")

df_curated = get_metadata_info(session, curated_bucket, model_type)

curated_df = create_curated_report(df_curated)

cell_renderer =  JsCode("""
function(params) {return `${params.value}`}
""")

options_builder = GridOptionsBuilder.from_dataframe(curated_df) 
options_builder.configure_selection("single") 
options_builder.configure_grid_options(enableRangeSelection=True)
options_builder.configure_grid_options(copyHeadersToClipboard=True)
grid_options = options_builder.build()

grid_return = AgGrid(curated_df, grid_options, fit_columns_on_grid_load=True, allow_unsafe_jscode=True) 
selected_rows = grid_return["selected_rows"]

st.write(selected_rows)

with open('./style.css') as css: st.markdown(css.read(), unsafe_allow_html=True)