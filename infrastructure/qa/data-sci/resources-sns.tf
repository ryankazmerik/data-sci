resource "aws_sns_topic_subscription" "data_sci_slack_lambda_topic_sub" {
  count = var.enable_slack_integration ? 1 : 0

  depends_on = [
    module.data_sci_slack_lambda
  ]

  topic_arn = data.terraform_remote_state.account.outputs.sns_topic_arns["data_sci_slack"]
  protocol  = "lambda"
  endpoint  = module.data_sci_slack_lambda[0].lambda_arn

  filter_policy = <<EOF
{
  "topic_name": [{"exists": true}],
  "model": [{"exists": true}],
  "pipeline": [{"exists": true}],
  "environment": [{"exists": true}]
}
EOF
}
