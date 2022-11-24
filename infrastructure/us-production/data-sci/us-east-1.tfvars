aws_account_id                              = "314383152509"
aws_account_alias                           = "stlr-us"
aws_account_email                           = "aws-us@stellaralgo.com"
account_name                                = "us"
deployment_role                             = "tf-deployment"
workspace                                   = "us-east-1"
environment                                 = "prod"
region                                      = "us-east-1"
owner                                       = "StellarAlgo"

enable_sagemaker_studio                     = true
enable_sagemaker_notebooks                  = false
enable_slack_integration                    = false

include("us-east-1.tfvars.d/*.tfvars")