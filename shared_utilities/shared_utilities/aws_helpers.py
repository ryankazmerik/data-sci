import boto3
import json


def _get_ssm_parameter_value(parameter_name: str):

    ssm_client = boto3.client("ssm")
    client_reponse = ssm_client.get_parameter(Name=parameter_name)

    return client_reponse["Parameter"]["Value"]


def _client_uses_elbu_cluster(lkupclientid) -> bool:

    return int(lkupclientid) in [96, 98, 99, 100]

def get_cluster_endpoints():

    ssm_param = ("/data-sci/redshift/cluster_endpoints")
    cluster_endpoints = json.loads(_get_ssm_parameter_value(ssm_param))

    return cluster_endpoints

def get_cluster_name(lkupclientid: int) -> str:
    ssm_param = ("/model/data-sci-product-propensity/redshift/cluster_environment") + '-app'

    cluster_name = _get_ssm_parameter_value(ssm_param)

    if _client_uses_elbu_cluster(lkupclientid):
        cluster_name += "-elbu"

    return cluster_name

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