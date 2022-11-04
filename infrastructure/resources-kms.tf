module "model_kms_key" {
  source = "../../infrastructure-common/modules/kms_key"

  key_description     = format("KMS key for model %s", local.model_name)
  key_alias           = local.model_name
  enable_key_rotation = true

  statements = merge(
    {
      AllowServiceAccess = {
        effect = "Allow"
        principals = {
          Service = [
            "s3.amazonaws.com",
            "states.amazonaws.com",
            "sagemaker.amazonaws.com",
            "ssm.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        }
        actions = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey",
          "kms:ListAliases",
          "kms:CreateGrant",
          "kms:RetireGrant",
          "kms:GenerateDataKeyWithoutPlaintext",
          "kms:GenerateDataKeyPair",
          "kms:GenerateDataKeyPairWithoutPlaintext"
        ]
        resources = ["*"]
      }

      AllowQADSAccess = {
        effect = "Allow"
        principals = {
          AWS = [
            one(data.aws_iam_roles.qa_StellarDataScienceAdmin.arns)
          ]
        }
        actions = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        resources = ["*"]
      }

      AllowSupportAccess = {
        effect = "Allow"
        principals = {
          AWS = [
            one(data.aws_iam_roles.us_StellarSupport.arns)
          ]
        }
        actions = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        resources = ["*"]
      }

      AllowLegacyDSAccess = {
        effect = "Allow"
        principals = {
          AWS = [
            "arn:aws:iam::173696899631:role/datascience-redshift-etl"
          ]
        }
        actions = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        resources = ["*"]
      }
    }
  )

  tags = local.tags
}
