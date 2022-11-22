aws_account_id                              = "176624903806"
aws_account_alias                           = "stlr-exp-us"
aws_account_email                           = "aws-explore-us@stellaralgo.com"
account_name                                = "explore-us"
deployment_role                             = "tf-deployment"
workspace                                   = "explore-us.us-east-1"
environment                                 = "explore"
region                                      = "us-east-1"

deploy_retention                            = true
deploy_product_propensity                   = true

deploy_training                             = true
enable_training_trigger                     = false

deploy_inference                            = true
enable_inference_trigger                    = false

table_load_event_source                     = "na"

include("explore-us.tfvars.d/us-east-1/*.tfvars")