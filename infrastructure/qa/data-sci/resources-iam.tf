module "sagemaker_notebook_default_role" {
  count = var.enable_sagemaker_notebooks ? 1 : 0

  depends_on = [
    module.data_sci_experiments_s3
  ]

  source           = "../../../../infrastructure-common/modules/iam_role"
  role_name        = "default-notebook-instance"
  role_description = "Role used by data sci notebook instance(s)"

  attached_policies = []

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
            "arn:aws:ssm:${var.region}:${var.aws_account_id}:parameter/data-sci/*"
          ]
        }
      }
    }

    "S3" = {
      statements = {
        "AllowS3RW" = {
          effect = "Allow"
          actions = [
            "s3:List*",
            "s3:Put*",
            "s3:Get*"
          ]
          resources = [
            module.data_sci_experiments_s3[0].s3_bucket_arn
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
              test = "StringEquals"
              variable = "sts:AWSServiceName"
              values = [ "codeartifact.amazonaws.com" ]
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

module "sagemaker_studio_default_role" {
  count = var.enable_sagemaker_studio ? 1 : 0

  source           = "../../../../infrastructure-common/modules/iam_role"
  role_name        = "${var.environment}-sagemaker-studio-default"
  role_description = "Default role used by sagemaker studio instance(s)."

  attached_policies = [
    "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
  ]

  inline_policies = {
    "KMS" = {
      statements = {
        "AllowDecrypt" = {
          effect = "Allow"
          actions = [
            "kms:Decrypt",
            "kms:Encrypt",
            "kms:DescribeKey",
            "kms:ListAliases",
            "kms:CreateGrant",
            "kms:RetireGrant",
            "kms:GenerateDataKey",
            "kms:GenerateDataKeyWithoutPlaintext",
            "kms:GenerateDataKeyPair",
            "kms:GenerateDataKeyPairWithoutPlaintext"
          ]
          resources = [
            # Each models kms key goes here retention, product propensity
            "*"
            # "arn:aws:iam:${var.region}:${var.aws_account_id}:alias/aws/ssm"
          ]
        }
      }
    }

    "S3" = {
      statements = {
        "AllowS3List" = {
          effect = "Allow"
          actions = [
            "s3:List*"
          ]
          resources = [
            "arn:aws:s3:::${var.account_name}-model-data-sci-*-${var.region}-*"
          ]
        }

        "AllowS3Get" = {
          effect = "Allow"
          actions = [
            "s3:Get*"
          ]
          resources = [
            "arn:aws:s3:::${var.account_name}-model-data-sci-*-${var.region}-*/*"
          ]
        }
      }
    }

    # "SSM" = {
    #   statements = {
    #     "AllowGetSSM" = {
    #       effect = "Allow"
    #       actions = [
    #         "ssm:Describe*",
    #         "ssm:Get*",
    #         "ssm:List*"
    #       ]
    #       resources = [
    #         "arn:aws:ssm:${var.region}:${var.aws_account_id}:parameter/data-sci/*"
    #       ]
    #     }
    #   }
    # }
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

module "data_sci_slack_lambda_role" {
  count = var.enable_slack_integration ? 1 : 0

  depends_on = [
    resource.random_string.random_role_id
  ]

  source           = "../../../../infrastructure-common/modules/iam_role"
  role_name        = "data-sci-slack-sns-lambda-${resource.random_string.random_role_id.result}"
  role_description = "Role used by the slack messaging lambda."

  attached_policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  inline_policies = {
    "KMS" = {
      statements = {
        "AllowKMSDecrypt" = {
          effect = "Allow"
          actions = [
            "kms:Decrypt",
            "kms:GenerateDataKey",
            "kms:GenerateDataKeyWithoutPlaintext",
            "kms:GenerateDataKeyPair",
            "kms:GenerateDataKeyPairWithoutPlaintext"
          ],
          resources = [
            data.terraform_remote_state.account.outputs.account_kms_key.arn
          ]
        }
      }
    }

    "SSM" = {
      statements = {
        "SSMReadOnlyAccess" = {
          effect = "Allow"
          actions = [
            "ssm:Get*"
          ],
          resources = [
            aws_ssm_parameter.ialerts_ai_slack_hook_url[0].arn
          ]
        }
      }
    }
  }

  trust_relationships = {
    AllowLambda = {
      principals = {
        Service = [
          "lambda.amazonaws.com"
        ]
      }
    }
  }

  tags = local.tags
}
