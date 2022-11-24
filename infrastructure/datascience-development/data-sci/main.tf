provider "aws" {
  alias  = "origin"
  region = var.region
}

provider "aws" {
  allowed_account_ids = [local.aws_account_id]
  region              = var.region

  assume_role {
    role_arn    = "arn:aws:iam::${local.aws_account_id}:role/${var.deployment_role}"
    external_id = "4675845643"
  }
}

terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">= 2.2.2"
    }

    aws = {
      source  = "hashicorp/aws"
      version = "= 4.21"
    }

    random = {
      source  = "hashicorp/random"
      version = "= 3.1.0"
    }
  }

  backend "s3" {
    bucket         = "stellaralgo-tf-states-us-east-1"
    key            = "explore-us/data-sci.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-state-locks"
  }
}
