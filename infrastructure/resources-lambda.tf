module "retention_dw_lambda" {
  count = var.deploy_retention ? 1 : 0
  # for_each = toset(local.pipelines)

  source = "../../infrastructure-common/modules/lambda_function"

  depends_on = [
    module.dw_iam_role,
    module.dw_lambda_sg
  ]

  name         = "${local.model_name}-retention"
  description  = "The lambda that runs a full train & inference job for teams on MSSQL."
  package_type = "Image"
  memory_size  = 4096
  timeout      = 600

  function_image_uri = "${module.dw_ecr_repository_retention[0].repository_url}:latest"

  image_config = {
    entry_point       = null
    command           = ["pipeline.run"]
    working_directory = null
  }

  #   environment_variables = {
  #     MODEL_BUCKET     = module.model_s3_bucket.s3_bucket_name
  #     TRIGGER_FUNCTION = module.training_run_pipeline_lambda[0].function_name
  #   }

  iam_role_arn       = module.dw_iam_role[0].iam_role_arn
  security_group_ids = [module.dw_lambda_sg[0].security_group_id]
  subnet_ids         = values(data.terraform_remote_state.account.outputs.vpc_networks["main"].private_subnet_ids["data"])

  tags = local.tags
}
