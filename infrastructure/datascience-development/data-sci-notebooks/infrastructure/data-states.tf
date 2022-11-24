data "aws_caller_identity" "current" {}

data "terraform_remote_state" "account" {
  backend = "s3"

  config = {
    bucket = "stellaralgo-tf-states-us-east-1"
    key    = "env:/${var.region}/${var.account_name}/main.tfstate"
    region = "us-east-1"
  }
}
