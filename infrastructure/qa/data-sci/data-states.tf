data "terraform_remote_state" "account" {
  backend = "s3"

  config = {
    bucket = "stellaralgo-tf-states-us-east-1"
    key    = "env:/${var.region}/${var.account_name}/main.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "code_common" {
  backend = "s3"

  config = {
    bucket = "stellaralgo-tf-states-us-east-1"
    key    = "common/${var.account_name}.${var.region}/main.tfstate"
    region = "us-east-1"
  }
}

data "aws_caller_identity" "current" {}

data "aws_caller_identity" "origin" {
  provider = aws.origin
}
