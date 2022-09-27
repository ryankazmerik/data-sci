import boto3
import sys
import json
from boto3.s3.transfer import TransferConfig
from datetime import datetime, timezone
from urllib.parse import urlparse
import questionary


config = TransferConfig(multipart_threshold=1024 * 50, 
                        max_concurrency=20,
                        multipart_chunksize=1024 * 50,
                        use_threads=True)

env_config = {
    "qa": {
        "aws_account_id": "564285676170",
        "destination_environment": "qa",
        "aws_profile_name": "qa-admin",
        "subnets": ["subnet-016a23a22d09bac9b", "subnet-03e755df7e78d56f1"],
        "sgs": ["sg-053b15ed15d46581a"],
        "previous_env_iam_arn": "arn:aws:iam::176624903806:role/ai-deploy-model-retention" # this would be explore for QA
    },
    "us": {
        "aws_account_id": "314383152509",
        "destination_environment": "us",
        "aws_profile_name": "us-support",
        "subnets": ["subnet-05da3f2092b77f05e", "subnet-0da584734b2fc368a"],
        "sgs": ["sg-0ca66936278330b2c"],
        "previous_env_iam_arn": "arn:aws:iam::176624903806:role/ai-deploy-model-retention" # this would be QA for US
    }
}

qa = boto3.setup_default_session(profile_name="QA-DS-Admin")
sagemaker_client = boto3.client("sagemaker", region_name="us-east-1")
ssm_client = boto3.client("ssm", region_name="us-east-1")

# explore = boto3.Session(profile_name="Explore-US-DataScienceAdmin")
# explore_sagemaker_client = explore.client("sagemaker", region_name="us-east-1")

def main():

    env_to_promote_to = questionary.select(
        "What environment do you want to promote TO?",
        choices=["qa", "us"],
    ).ask()

    selected_env = env_config[env_to_promote_to]

    model_config = {
        "retention": {
            "random_bucket_id": "a" if env_to_promote_to == "qa" else "b",
            "role_name": "a" if env_to_promote_to == "qa" else "b"
        },
        "product-propensity": {
            "random_bucket_id": "mgwy8o" if env_to_promote_to == "qa" else "d2n55o",
            "role_name": "data-sci-product-propensity-pipeline-t6qwkf" if env_to_promote_to == "qa" else "data-sci-product-propensity-pipeline-jxswaj"
        },
        "event-propensity": {
            "random_bucket_id": "a" if env_to_promote_to == "qa" else "b",
            "role_name": "a" if env_to_promote_to == "qa" else "b"
        }
    }

    model = questionary.select(
        "What model do you want to promote? (Retention won't work until new retention refactor is done)",
        choices=["product-propensity", "event-propensity"],
    ).ask()

    selected_model = model_config[model]

    result = _get_sagemaker_models(model)
    teams = [x["ModelName"] for x in result["Models"]]
    print(teams)

    # questionary.checkbox(f'Select teams to promote to {env_to_promote_to}',choices=teams).ask()

    # assume_iam_role(selected_env["previous_env_iam_arn"])
    # print("getting sm models")
    # s3 = boto3.client("s3", region_name="us-east-1")

    # s3.list_objects_v2(Bucket="explore-us-model-data-sci-" + model + "-us-east-1-" + selected_model["random_bucket_id"], Prefix="training")

    # result = sagemaker_client.list_models(MaxResults=100, NameContains=model_chosen)
    print(result)
    model_chosen = teams[0]
    # model_chosen = result["Models"][0]["ModelName"]
    print(model_chosen)
    print(type(model_chosen))
    print(sagemaker_client.describe_model(ModelName=model_chosen))
    print("done")

    # boto3.setup_default_session(region_name="us-east-1")
    # result = _get_sagemaker_models(model)
    # print(result)

    # Get SSM for each env and display and get input

    ## Here I can get diffs for QA and PROD SSM for the specific envs and teams (explore and QA, or QA and US)
    ## Display the diff to the user (maybe as a table)
    ## Ask user which teams to promote
    teams = []

    # questionary.checkbox(

    # f'Select teams to promote to {env_to_promote_to}',

    # choices=teams).ask()

# Run promote logic

# Done

def _get_sagemaker_models(substring):
    try:
        return sagemaker_client.list_models(MaxResults=100, NameContains=substring)
    except Exception as e:
        print(e)

def _get_ssm_param(ssm_parameter_path):
    #  = f"/model/data-sci-{product}/deployed_model_names"
    try:
        ssm_parameter = ssm_client.get_parameter(
            Name=ssm_parameter_path,
            WithDecryption=True
        )

        return ssm_parameter

    except Exception as e:
        raise Exception(f"Unknown SSM error: {e}")


def assume_iam_role(role_arn: str):

    sts_client = boto3.client("sts")

    sts_response = sts_client.assume_role(
        RoleArn=role_arn, RoleSessionName="ds_session",
    )

    session_id = sts_response["Credentials"]["AccessKeyId"]
    session_key = sts_response["Credentials"]["SecretAccessKey"]
    session_token = sts_response["Credentials"]["SessionToken"]

    boto3.setup_default_session(
        region_name="us-east-1",
        aws_access_key_id=session_id,
        aws_secret_access_key=session_key,
        aws_session_token=session_token,
    )



if __name__ == "__main__":
    main()