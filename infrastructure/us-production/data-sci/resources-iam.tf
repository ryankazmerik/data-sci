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
