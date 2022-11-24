# This file contains the terraform provider and backend setup.

provider "aws" {
  allowed_account_ids = [local.aws_account_id]
  region              = var.region

  assume_role {
    role_arn     = "arn:aws:iam::${local.aws_account_id}:role/${var.deployment_role}"
    # session_name = ""
    external_id  = "4675845643"
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
      version = "= 4.14"
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
    workspace_key_prefix = "products/ai-pipeline"
  }
}
