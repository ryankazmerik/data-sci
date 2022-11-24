aws_account_id                              = "564285676170"
aws_account_alias                           = "stlr-qa"
aws_account_email                           = "aws-qa@stellaralgo.com"
account_name                                = "qa"
deployment_role                             = "tf-deployment"
workspace                                   = "us-east-1"
environment                                 = "qa"
region                                      = "us-east-1"
owner                                       = "data-sci"

enable_sagemaker_studio                     = true
enable_sagemaker_notebooks                  = false
enable_slack_integration                    = false

include("us-east-1.tfvars.d/*.tfvars")