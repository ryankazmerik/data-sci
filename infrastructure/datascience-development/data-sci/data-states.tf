data "aws_caller_identity" "current" {}

data "aws_caller_identity" "origin" {
  provider = aws.origin
}

data "terraform_remote_state" "account" {
  backend = "s3"

  config = {
    bucket = "stellaralgo-tf-states-us-east-1"
    key    = "env:/${var.workspace}/${var.account_name}/main.tfstate"
    region = "us-east-1"
  }
}
