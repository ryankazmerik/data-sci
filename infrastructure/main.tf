# This file contains the terraform provider and backend setup.
provider "aws" {
  alias  = "origin"
  region = var.region
}

provider "aws" {
  allowed_account_ids = [local.aws_account_id]
  region              = var.region

  assume_role {
    role_arn     = "arn:aws:iam::${local.aws_account_id}:role/${var.deployment_role}"
    session_name = split("/", data.aws_caller_identity.origin.arn)[2]
    external_id  = "4675845643"
  }
}

provider "aws" {
  alias               = "explore-us"
  allowed_account_ids = ["176624903806"]
  region              = var.region

  assume_role {
    role_arn = "arn:aws:iam::176624903806:role/${var.deployment_role}"
    # session_name = ""
    external_id = "4675845643"
  }
}

provider "aws" {
  alias               = "qa"
  allowed_account_ids = ["564285676170"]
  region              = var.region

  assume_role {
    role_arn = "arn:aws:iam::564285676170:role/${var.deployment_role}"
    # session_name = ""
    external_id = "4675845643"
  }
}

provider "aws" {
  alias               = "us"
  allowed_account_ids = ["314383152509"]
  region              = var.region

  assume_role {
    role_arn = "arn:aws:iam::314383152509:role/${var.deployment_role}"
    # session_name = ""
    external_id = "4675845643"
  }
}

terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">= 1.2"
    }

    aws = {
      source  = "hashicorp/aws"
      version = "= 4.11.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "= 3.1.0"
    }
  }

  backend "s3" {
    bucket               = "stellaralgo-tf-states-us-east-1"
    key                  = "main.tfstate"
    region               = "us-east-1"
    workspace_key_prefix = "data-sci/dw"
  }
}
