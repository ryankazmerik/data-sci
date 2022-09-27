import io
import boto3
import botocore
import json
import subprocess

from boto3.s3.transfer import TransferConfig
from datetime import datetime

class BaseHandler:
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

    region = "us-east-1"

    config = TransferConfig(multipart_threshold=1024 * 50, 
                        max_concurrency=20,
                        multipart_chunksize=1024 * 50,
                        use_threads=True)
    
    # If any need to be different, we can change it here. I'd like to make them all the same though
    sagemaker_model_name = {
        "retention": "data-sci-:model:-:model_subtype:-:date:",
        "product_propensity": "data-sci-:model:-:model_subtype:-:date:",
        "event_propensity": "data-sci-:model:-:model_subtype:-:date:"
    }

    def __init__(self, model, is_old) -> None:

        if is_old:
            self.session = self._create_session_old()
        else:
            self.session = self._create_session()
        self.model = model
        self.sagemaker_client = self.session.client("sagemaker")
        self.ssm_client = self.session.client("ssm")
        self.random_bucket_id = self.random_bucket_id[self.model]

    def __str__(self) -> str:
        return f"{self.environment},{self.model},{self.subnets},{self.security_groups},{self.random_bucket_id}"

    def _create_session(self):
        # temp_session = boto3.session.Session()
        # return temp_session
        # sts = boto3.client("sts")
        # print(f"Test: {sts.get_caller_identity()}")
        # credentials = sts.assume_role(**self.role_info)
        # identity = sts.get_caller_identity()
        # credentials = sts.assume_role(RoleArn=identity["Arn"], RoleSessionName=f"{self.profile}")
        # credentials = sts.get_session_token()

        # session = boto3.Session(profile_name=self.profile)
        aws_access_key_id, aws_secret_access_key, aws_session_token = self._get_aws_vault_credentials(self.profile)
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name="us-east-1",
            profile_name=self.profile
        )
        print(f"Profiles: {session.available_profiles}")
        print(f"Profile: {session.profile_name}")
        print(f"Resources: {session.get_available_resources()}")
        return session
    
    def _get_aws_vault_credentials(self, aws_profile):
        envvars = subprocess.check_output(['aws-vault', 'exec', aws_profile, '--', 'env'])
        for envline in envvars.split(b'\n'):
            line = envline.decode('utf8')
            eqpos = line.find('=')
            if eqpos < 4:
                continue
            k = line[0:eqpos]
            v = line[eqpos+1:]
            if k == 'AWS_ACCESS_KEY_ID':
                aws_access_key_id = v
            if k == 'AWS_SECRET_ACCESS_KEY':
                aws_secret_access_key = v
            if k == 'AWS_SESSION_TOKEN':
                aws_session_token = v
        return aws_access_key_id, aws_secret_access_key, aws_session_token
    
    def _create_session_old(self, retry = True):
        session = boto3.Session(profile_name=self.profile)
        sts = session.client('sts')
        try:
            identity = sts.get_caller_identity()
            print(f"Authorized as {identity['UserId']}")
            return session
        except botocore.exceptions.UnauthorizedSSOTokenError:
            if retry:
                subprocess.run(['aws','sso', 'login', '--profile', self.profile])
                return self._create_session_old(False)
            else:
                raise
    
    def _get_model_bucket_name(self):
        return f"{self.environment.lower()}-model-data-sci-{self.model}-{self.region}-{self.random_bucket_id}"
    
    def _get_sagemaker_models(self):
        try:
            response = self.sagemaker_client.list_model_package_groups(MaxResults=100, NameContains=self.model, SortBy="Name", SortOrder="Ascending")
            package_groups = response["ModelPackageGroupSummaryList"]
            # models = self.sagemaker_client.list_models(MaxResults=100)
            i = 0
            while "NextToken" in response:
                i += 1
                print(i)
                response = self.sagemaker_client.list_model_package_groups(MaxResults=100, NameContains=self.model, SortBy="Name", SortOrder="Ascending", NextToken=response["NextToken"])
                package_groups.extend(response["ModelPackageGroupSummaryList"])

            return package_groups
        except Exception as e:
            raise Exception(f"Unkown exception listing models: {e}")
    
    def get_model_package_descriptions(self, model_group_name):
        packages = self.sagemaker_client.list_model_packages(ModelPackageGroupName=model_group_name)
        # We get the item with index 0 because its the newest version
        description = self.sagemaker_client.describe_model_package(ModelPackageName=packages["ModelPackageSummaryList"][0]["ModelPackageArn"])
        return description
    
    def get_promotable_models(self):
        """Gets the list of promotable model names from SageMaker. Removes ARN, CreationTime, and NextToken. These can be changed if needed.

        Returns:
            _type_: _description_
        """
        return self._get_sagemaker_models()

    def _get_model_description(self, model_name: str):
        try:
            return self.sagemaker_client.describe_model(ModelName=model_name)
        except Exception as e:
            raise Exception(f"Unknown exception describing model with model name {model_name} - {e}")

    def get_promote_info_from_list(self, model_names: list):
        promote_info_list = []
        for model_name in model_names:
            promote_info_list.append(self._get_model_description(model_name))
        return promote_info_list
    
    def _register_model(self, model_name, model_subtype, container_image, destination_bucket, destination_key, training_id):
        date = str(datetime.now()).split(" ")[0]
        try:
            response = self.sagemaker_client.create_model(
                ModelName=model_name,
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

                ExecutionRoleArn=f"arn:aws:iam::{self.aws_account_id}:role/{self.role_name}",
                Tags=[
                    {
                        "Key": "model",
                        "Value": self.model
                    },
                    {
                        "Key": "model_subtype",
                        "Value": model_subtype
                    },
                    {
                        "Key": "environment",
                        "Value": self.environment.lower()
                    },
                    {
                        "Key": "region",
                        "Value": self.region
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
                    "SecurityGroupIds": self.security_groups,
                    "Subnets": self.subnets
                },
                EnableNetworkIsolation=True
            )

            print(response)
        except Exception as e:
            print("ERROR: Could not create sagemaker model.")
            print(e)

    def _update_ssm_param(self, model_name, model_subtype):
        ssm_parameter_path = f"/model/data-sci-{self.model}/deployed_model_names"

        try:
            ssm_parameter = self.ssm_client.get_parameter(
                Name=ssm_parameter_path,
                WithDecryption=True
            )

            print(ssm_parameter)

        except Exception as e:
            print("ERROR: Parameter was not successfully retrieved.")
            print(e)

        ssm_payload = json.loads(ssm_parameter["Parameter"]["Value"]) 
        ssm_payload[model_subtype] = model_name

        try:
            response = self.ssm_client.put_parameter(
                Name=ssm_parameter_path,
                Value=json.dumps(ssm_payload),
                Type="String",
                Overwrite=True
            )

            print(response)
        except Exception as e:
            print("ERROR: Parameter was not successfully updated.")
            print(e)

    def _download_from_bucket(self, bucket, key):
        bucket = bucket.replace("s3://", "")
        print("1")
        s3_client = self.session.resource("s3")
        print("2")
        obj = s3_client.Object(bucket, key)
        print(f"3: {obj}")
        io_stream = io.BytesIO()
        obj.download_fileobj(io_stream)
        print("4")
        io_stream.seek(0)
        print("5")
        return io_stream

        

    def promote_model(self, model_name, model_subtype, container_image, source_bucket, source_key, training_id):
        # test = self._download_from_bucket(source_bucket, source_key)
        # print(test)
        copy_source = {
            "Bucket": source_bucket,
            "Key": source_key
        }

        s3_client = self.session.resource("s3")
        target_bucket = self._get_model_bucket_name()
        s3_bucket = s3_client.Bucket(target_bucket)
        obj = s3_bucket.Object(source_key)

        # test = self._download_from_bucket(source_bucket, source_key)
        # print(test)


        print(f"\ntarget bucket: {s3_bucket}\ntarget key: {obj}\nsource: {copy_source}")
        obj.copy(
            CopySource = copy_source,
            ExtraArgs={"ACL": "bucket-owner-full-control"},
            Config=self.config
        )
        print("Done copying")

        date = str(datetime.now()).split(" ")[0]
        full_model_name = f"{model_name}-{date}"

        self._register_model(full_model_name, model_subtype, container_image, target_bucket, source_key, training_id)
        self._update_ssm_param(full_model_name, model_subtype)
        
