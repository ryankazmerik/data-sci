import boto3
import botocore
import subprocess
import questionary

from explorehandler import ExploreHandler
from qahandler import QAHandler
from urllib.parse import urlparse


def main():
    model = questionary.select(
        "What model do you want to promote? (Retention won't work until new retention refactor is done)",
        choices=["retention", "product-propensity", "event-propensity"],
    ).ask()

    env_to_promote_to = questionary.select(
        "What environment do you want to promote TO?",
        choices=["QA", "US"],
    ).ask()
    
    if env_to_promote_to == "QA":
        old_env = ExploreHandler(model=model, is_old=True)
        new_env = QAHandler(model=model, is_old=False)
    else:
        pass
    
    print(old_env)
    list_of_models_old = old_env.get_promotable_models()
    # print(list_of_models_old)
    models_to_promote = questionary.checkbox(
        f'Select teams to promote to {env_to_promote_to}',
        choices=[model["ModelPackageGroupName"] for model in list_of_models_old]).ask()
    # print(list_of_models_old)
    model_arns = [model["ModelPackageGroupArn"] for model in list_of_models_old if model["ModelPackageGroupName"] in models_to_promote]
    for model_arn in model_arns:
        description = old_env.get_model_package_descriptions(model_arn)
        print(f"\nPromoting:\nModel: {description['ModelPackageGroupName']}\nVersion: {description['ModelPackageVersion']}\nCreation Date: {description['CreationTime']}\nS3 Path: {description['InferenceSpecification']['Containers'][0]['ModelDataUrl']}")
        s3_url_parsed = urlparse(description['InferenceSpecification']['Containers'][0]['ModelDataUrl'], allow_fragments=False)

        model_subtype = "-".join(description["ModelPackageGroupName"].split("-")[-2:])
        bucket_name = s3_url_parsed.netloc
        bucket_key  = s3_url_parsed.path

        split_bucket = description['InferenceSpecification']['Containers'][0]['ModelDataUrl'].replace("s3://", "").split("/")

        training_id = [item for item in split_bucket if "TrainingStep" in item][0]
        print(f"Training ID: {training_id}")

        container_image = description["InferenceSpecification"]["Containers"][0]["Image"]

        # print(new_env._download_from_bucket(bucket_name, bucket_key))

        # try:
        new_env.promote_model(description["ModelPackageGroupName"], model_subtype, container_image, bucket_name, bucket_key, training_id)
        # except Exception as e:
        #     print(f"Unknown exception occurred when promoting model: {e}")

    
    # model_descriptions = old_env.get_promote_info_from_list(models_to_promote)

    # try:
    #     for model_desc in model_descriptions:
    #         model_name = model_desc["ModelName"]
    #         model_s3_path = model_desc["PrimaryContainer"]["ModelDataUrl"]

    #         s3_url_parsed = urlparse(model_s3_path, allow_fragments=False)

    #         bucket_name = s3_url_parsed.netloc
    #         bucket_key  = s3_url_parsed.path

    #         result = new_env.promote_models(model_name, bucket_name, bucket_key)
    # except Exception as e:
    #     print(f"Failed to promote models with exception raised: {e}")

    # if result["status"] == "Success":
    #     print(f"Successfully promoted {len(result['promoted_models'])} models to {env_to_promote_to}")
    #     print(f"Promoted the following models: {result['promoted_models']}")
    

if __name__ == "__main__":
    main()