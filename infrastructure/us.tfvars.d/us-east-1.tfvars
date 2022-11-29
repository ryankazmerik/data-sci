aws_account_id                              = "314383152509"
aws_account_alias                           = "stlr-us"
aws_account_email                           = "aws-us@stellaralgo.com"
account_name                                = "us"
deployment_role                             = "tf-deployment"
workspace                                   = "us.us-east-1"
environment                                 = "prod"
region                                      = "us-east-1"

deploy_retention                            = true
deploy_product_propensity                   = true

deploy_training                             = true
enable_training_trigger                     = false

deploy_inference                            = true
enable_inference_trigger                    = false

table_load_event_source                     = "na"

include("us.tfvars.d/us-east-1/*.tfvars")