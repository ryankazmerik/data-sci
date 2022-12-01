module "dw_role_policy" {
  count = var.deploy_retention || var.deploy_product_propensity ? 1 : 0

  source             = "../../infrastructure-common/modules/iam_policy"
  policy_name        = format("%s-policy-%s", local.model_name, random_string.random_role_id.result)
  policy_path        = "/"
  policy_description = format("Policy for run pipeline role.")
  document_version   = "2012-10-17"

  statements = {
    "AllowKMS" = {
      effect = "Allow"
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
      resources = var.environment == "prod" ? local.kms_prod_resources : local.kms_explore_resources
    }

    "AllowS3Read" = {
      effect = "Allow"
      actions = [
        "s3:Get*"
      ]
      resources = [
        "*"
      ]
    }

    "AllowS3Write" = {
      effect = "Allow"
      actions = [
        "s3:Put*"
      ]
      resources = [
        "*"
      ]
    }

    "ReadSSMParameters" = {
      effect = "Allow"
      actions = [
        "ssm:Get*"
      ]
      resources = [
        "arn:aws:ssm:${var.region}:${var.aws_account_id}:parameter/data-sci/*"
      ]
    }

    "DescribeSSMParameters" = {
      effect = "Allow"
      actions = [
        "ssm:DescribeParameters"
      ]
      resources = [
        "*"
      ]
    }

    "AssumeRedshiftETLRole" = {
      effect = "Allow"
      actions = [
        "sts:AssumeRole"
      ]
      resources = [
        "arn:aws:iam::173696899631:role/datascience-redshift-etl"
      ]
    }
  }
}

module "dw_iam_role" {
  count = var.deploy_retention || var.deploy_product_propensity ? 1 : 0

  depends_on = [
    module.dw_role_policy
  ]

  source           = "../../infrastructure-common/modules/iam_role"
  role_name        = format("%s-pipeline-%s", local.model_name, random_string.random_role_id.result)
  role_description = "Assumable role by pipeline lambdas to access resources."

  attached_policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    module.dw_role_policy[0].iam_policy_arn
  ]

  trust_relationships = {
    AllowSageMaker = {
      principals = {
        Service = [
          "lambda.amazonaws.com",
        ],
        AWS = [
          "arn:aws:iam::173696899631:role/datascience-redshift-etl"
        ]
      }
    }
  }
}
