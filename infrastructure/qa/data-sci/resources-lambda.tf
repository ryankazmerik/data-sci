module "data_sci_slack_lambda" {
  count = var.enable_slack_integration ? 1 : 0

  source = "../../../../infrastructure-common/modules/lambda_function"

  depends_on = [
    module.data_sci_slack_lambda_sg,
    module.data_sci_slack_lambda_role
  ]

  name          = "data-sci-slack-sns"
  description   = "The lambda that is subscribed to certain sns topics and relays messages to slack"
  timeout       = 60
  runtime       = var.data_sci_slack_lambda_runtime
  handler       = var.data_sci_slack_lambda_handler
  filename      = "${path.module}/zips/slack_sns_lambda.zip"
  filename_hash = data.archive_file.data_sci_slack_lambda[0].output_base64sha256
  iam_role_arn  = module.data_sci_slack_lambda_role[0].iam_role_arn

  security_group_ids = [
    data.terraform_remote_state.account.outputs.vpc_networks["main"].endpoint_security_group_ids["ssm"],
    module.data_sci_slack_lambda_sg[0].security_group_id
  ]

  subnet_ids = values(data.terraform_remote_state.account.outputs.vpc_networks["main"].private_subnet_ids["data"])
  layers     = [data.terraform_remote_state.code_common.outputs.utility_layer_arn]
  tags       = local.tags
}

resource "aws_lambda_permission" "with_sns" {
  count = var.enable_slack_integration ? 1 : 0

  depends_on = [
    module.data_sci_slack_lambda
  ]

  statement_id  = "AllowExecutionFromDataSciSlackSNS"
  action        = "lambda:InvokeFunction"
  function_name = module.data_sci_slack_lambda[0].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = data.terraform_remote_state.account.outputs.sns_topic_arns["data_sci_slack"]
}
