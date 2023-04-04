module "data_sci_curated_access_policy" {
  source = "../../../../infrastructure-common/modules/iam_policy"

  policy_name        = "data-sci-curated-access-${resource.random_string.random_role_id.result}"
  policy_path        = "/"
  policy_description = "Policy for allowing access to data-sci curated resources."
  document_version   = "2012-10-17"

  statements = {
    "AllowKMSDecrypt" = {
      effect = "Allow"
      actions = [
        "kms:GenerateDataKey",
        "kms:Decrypt"
      ]
      resources = [
        "arn:aws:kms:us-east-1:176624903806:key/94c0ac7e-881c-46d0-9d6a-c8daf1641ad3",
        "arn:aws:kms:us-east-1:176624903806:key/c04fab4f-0fd8-440a-a3ac-bb0ede289ced",
        "arn:aws:kms:us-east-1:176624903806:key/2183b5e1-671b-48b7-b335-2ad05e17fb96",
        "arn:aws:kms:us-east-1:176624903806:key/8f1308ae-0e64-4c93-8910-791ed24b7972"
      ]
    }

    "AllowS3BucketAccess" = {
      effect = "Allow",
      actions = [
        "s3:ListBucket",
        "s3:ListAllBuckets",
        "s3:GetBucketLocation"
      ],
      resources = [
        "arn:aws:s3:::explore-model-retention-us-east-1-ai-oprj0o",
        "arn:aws:s3:::explore-us-curated-data-sci-retention-us-east-1-ut8jag",
        "arn:aws:s3:::explore-us-curated-data-sci-product-propensity-us-east-1-u8gldf",
        "arn:aws:s3:::explore-us-curated-data-sci-event-propensity-us-east-1-tykotu"
      ]
    }

    "AllowS3ObjectAccess" = {
      effect = "Allow",
      actions = [
        "s3:List*",
        "s3:Get*"
      ],
      resources = [
        "arn:aws:s3:::explore-model-retention-us-east-1-ai-oprj0o/*",
        "arn:aws:s3:::explore-us-curated-data-sci-retention-us-east-1-ut8jag/*",
        "arn:aws:s3:::explore-us-curated-data-sci-product-propensity-us-east-1-u8gldf/*",
        "arn:aws:s3:::explore-us-curated-data-sci-event-propensity-us-east-1-tykotu/*"
      ]
    }
  }
}

module "data_sci_curated_access_role" {
  source = "../../../../infrastructure-common/modules/iam_role"

  depends_on = [
    module.data_sci_curated_access_policy
  ]
  role_name        = "data-sci-curated-access-${resource.random_string.random_role_id.result}"
  role_description = "A role that can be assumed by other accounts to access data sci curated buckets."

  attached_policies = [
    module.data_sci_curated_access_policy.iam_policy_arn
  ]

  trust_relationships = {
    AllowCrossAccount = {
      principals = {
        # AWS = [

        # ]
        Service = [
          "lambda.amazonaws.com"
        ]
      }
    }
  }
}

module "sagemaker_studio_role" {
  count = var.enable_sagemaker_studio ? 1 : 0

  source           = "../../../../infrastructure-common/modules/iam_role"
  role_name        = "data-sci-sagemaker-studio-${resource.random_string.random_role_id.result}"
  role_description = "Role used by data sci sagemaker studio instance(s)"

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
            "kms:GenerateDataKey",
            "kms:CreateGrant"
          ]
          resources = [
            "arn:aws:kms:us-east-1:176624903806:key/cbe87dbe-99b5-4779-8fdc-2a91c284690b",
            "arn:aws:kms:us-east-1:176624903806:key/2183b5e1-671b-48b7-b335-2ad05e17fb96",
            "arn:aws:kms:us-east-1:176624903806:key/976f8621-89bf-4993-9ff8-70eae98ec137",
            "arn:aws:kms:us-east-1:176624903806:key/c04fab4f-0fd8-440a-a3ac-bb0ede289ced"
          ]
        }
      }
    }

    "S3" = {
      statements = {
        "AllowS3" = {
          effect = "Allow"
          actions = [
            "s3:*"
          ]
          resources = [
            "arn:aws:s3:::*-data-sci-*",
            "arn:aws:s3:::*-data-sci-*/*"
          ]
        }
      }
    }

    "AssumeRedshiftETLRole" = {
      statements = {
        "AllowAssumeRedshiftETLRole" = {
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
