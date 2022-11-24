aws_account_id                              = "176624903806"
aws_account_alias                           = "stlr-exp-us"
aws_account_email                           = "aws-explore-us@stellaralgo.com"
account_name                                = "explore-us"
deployment_role                             = "tf-deployment"
workspace                                   = "us-east-1"
environment                                 = "explore"
region                                      = "us-east-1"
owner                                       = "data-sci"

enable_sagemaker_studio                     = true
enable_sagemaker_notebooks                  = false

include("us-east-1.tfvars.d/*.tfvars")