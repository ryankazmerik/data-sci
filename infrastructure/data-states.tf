data "aws_organizations_organization" "current" {}

data "aws_caller_identity" "current" {}

data "aws_caller_identity" "origin" {
  provider = aws.origin
}

data "aws_iam_roles" "explore_us_StellarAdmin" {
  provider    = aws.explore-us
  name_regex  = "AWSReservedSSO_StellarAdmin_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

data "aws_iam_roles" "qa_StellarAdmin" {
  provider    = aws.qa
  name_regex  = "AWSReservedSSO_StellarAdmin_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

data "aws_iam_roles" "qa_StellarDataScienceAdmin" {
  provider    = aws.qa
  name_regex  = "AWSReservedSSO_StellarDataScienceAdmin_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

data "aws_iam_roles" "us_StellarAdmin" {
  provider    = aws.us
  name_regex  = "AWSReservedSSO_StellarAdmin_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

data "aws_iam_roles" "us_StellarSupport" {
  provider    = aws.us
  name_regex  = "AWSReservedSSO_StellarSupport_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

data "terraform_remote_state" "account" {
  backend = "s3"

  config = {
    bucket = "stellaralgo-tf-states-us-east-1"
    key    = "env:/${var.region}/${var.account_name}/main.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "data_sci" {
  backend = "s3"

  config = {
    bucket = "stellaralgo-tf-states-us-east-1"
    key    = "env:/${var.region}/${var.account_name}/data-sci.tfstate"
    region = "us-east-1"
  }
}

# data "terraform_remote_state" "data_sci_retention" {
#   backend = "s3"

#   config = {
#     bucket               = "stellaralgo-tf-states-us-east-1"
#     key                  = "explore-us/data-sci-retention.tfstate"
#     region               = "us-east-1"
#     workspace_key_prefix = "data-sci/retention"
#   }
# }
