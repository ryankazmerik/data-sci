resource "aws_ssm_parameter" "ialerts_ai_slack_hook_url" {
  count = var.enable_slack_integration ? 1 : 0

  name        = "/data-sci/slack/ialerts-ai/hook_url"
  description = "The slack hook url to send https requests"
  key_id      = data.terraform_remote_state.account.outputs.account_kms_key.key_id
  type        = "SecureString"
  value       = "changeme"

  lifecycle {
    ignore_changes = [
      tags,
      value
    ]
  }

  tags = local.tags
}

resource "aws_ssm_parameter" "ssm_db_connections" {
  for_each = var.enable_sagemaker_notebooks && length(var.database_connections) > 0 ? var.database_connections : {}

  name        = "/data-sci/db-connections/${each.key}"
  description = "The ${each.key} database connection data."
  key_id      = data.terraform_remote_state.account.outputs.account_kms_key.arn
  type        = "SecureString"

  value = jsonencode({
    "name"     = each.key
    "server"   = each.value.db_host
    "port"     = each.value.db_port
    "database" = each.value.database
    "username" = "changeme"
    "password" = "changeme"
  })

  tags = merge({
    "stellar:lifecycle" = "data-sci"
  }, local.tags)

  lifecycle {
    ignore_changes = [
      tags,
      value
    ]
  }
}