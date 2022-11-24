module "iam_role_notebook_instance" {
  count = var.enable_notebook ? 1 : 0

  depends_on = [
    module.s3_ai_experimentation
  ]

  source           = "../../../../../infrastructure-common/modules/iam_role"
  role_name        = "${var.environment}-${local.product_name}-notebook-instance"
  role_description = "Role used by ai notebook instance(s)"

  attached_policies = [

  ]

  inline_policies = {
    "KMS" = {
      statements = {
        "AllowDecrypt" = {
          effect = "Allow"
          actions = [
            "kms:Decrypt",
            "kms:GenerateDataKey"
          ]
          resources = [
            "*"
            # "arn:aws:iam:${var.region}:${var.aws_account_id}:alias/aws/ssm"
          ]
        }
      }
    }

    "SSM" = {
      statements = {
        "AllowGetSSM" = {
          effect = "Allow"
          actions = [
            "ssm:Describe*",
            "ssm:Get*",
            "ssm:List*"
          ]
          resources = [
            "arn:aws:ssm:${var.region}:${var.aws_account_id}:parameter/product/${local.product_name}/notebook/*",
            "arn:aws:ssm:${var.region}:${var.aws_account_id}:parameter/customer/*"
          ]
        }
      }
    }

    "S3" = {
      statements = {
        "AllowS3RW" = {
          effect = "Allow"
          actions = [
            "s3:*"
          ]
          resources = [
            module.s3_ai_experimentation[0].s3_bucket_arn
          ]
        }
      }
    }

    "Cloudwatch" = {
      statements = {
        "EnableCreationAndManagementOfRDSCloudwatchLogGroupsAndStreams" = {
          effect = "Allow"
          actions = [
            "logs:CreateLogStream",
            "logs:CreateLogGroup",
            "logs:DescribeLogStreams",
            "logs:PutLogEvents"
          ]
          resources = [
            "arn:aws:logs:*:*:log-group:/aws/sagemaker/NotebookInstances:*"
          ]
        }
      }
    }

    "SageMaker" = {
      statements = {
        "AllowSagemakerNotebookPolicy" = {
          effect = "Allow"
          actions = [
            "sagemaker:StopNotebookInstance",
            "sagemaker:DescribeNotebookInstance"
          ]
          resources = [
            "*"
          ]
        }
      }
    }

    "CodeArtifact" = {
      statements = {
        "AllowReadCodeArtifactRepositories" = {
          effect = "Allow"
          actions = [
            "codeartifact:List*",
            "codeartifact:Describe*",
            "codeartifact:Get*",
            "codeartifact:Read*"
          ]
          resources = [
            "*"
          ]
        }

        "AllowSTS" = {
          effect = "Allow"
          actions = [
            "sts:GetServiceBearerToken"
          ]
          resources = [
            "*"
          ]
          conditions = [
            {
              test     = "StringEquals"
              variable = "sts:AWSServiceName"
              values   = ["codeartifact.amazonaws.com"]
            }
          ]
        }
      }
    }
  }

  trust_relationships = {
    AllowLambda = {
      principals = {
        Service = [
          "sagemaker.amazonaws.com"
        ]
      }
    }
  }
}
