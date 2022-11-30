resource "aws_lambda_permission" "data_sci_dw_retention_weekly_trigger" {
  count = var.deploy_retention ? 1 : 0

  depends_on = [
    module.data_sci_dw_retention_weekly_trigger,
    module.retention_dw_lambda
  ]

  statement_id   = "AllowEventBridge"
  action         = "lambda:InvokeFunction"
  function_name  = module.retention_dw_lambda[0].function_name
  principal      = "events.amazonaws.com"
  source_account = var.aws_account_id
}

module "data_sci_dw_retention_weekly_trigger" {
  source = "../../infrastructure-common/modules/eventbridge_rule"
  count  = var.deploy_retention ? 1 : 0

  rule_name           = "trigger-${local.model_name}-retention"
  description         = "Sends human readable notifications when there are privileged (full access) logins."
  schedule_expression = "cron(0 16 ? * MON *)"

  targets = {
    LambdaFunction = {
      arn = module.retention_dw_lambda[0].lambda_arn

      input_transformer = {
        input_paths = {

        }
        input_template = <<-EOF
          {
            "env": "prod"
          }
          EOF
      }
    }
  }

  is_enabled = var.retention_trigger
}

resource "aws_lambda_permission" "data_sci_dw_product_propensity_weekly_trigger" {
  count = var.deploy_product_propensity ? 1 : 0

  depends_on = [
    module.data_sci_dw_product_propensity_weekly_trigger,
    module.product_propensity_dw_lambda
  ]

  statement_id   = "AllowEventBridge"
  action         = "lambda:InvokeFunction"
  function_name  = module.product_propensity_dw_lambda[0].function_name
  principal      = "events.amazonaws.com"
  source_account = var.aws_account_id
}

module "data_sci_dw_product_propensity_weekly_trigger" {
  source = "../../infrastructure-common/modules/eventbridge_rule"
  count  = var.deploy_product_propensity ? 1 : 0

  rule_name           = "trigger-${local.model_name}-product-propensity"
  description         = "Sends human readable notifications when there are privileged (full access) logins."
  schedule_expression = "cron(0 16 ? * MON *)"

  targets = {
    LambdaFunction = {
      arn = module.product_propensity_dw_lambda[0].lambda_arn

      input_transformer = {
        input_paths = {

        }
        input_template = <<-EOF
          {
            "env": "prod"
          }
          EOF
      }
    }
  }

  is_enabled = var.product_propensity_trigger
}
