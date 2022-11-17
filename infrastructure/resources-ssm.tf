resource "aws_ssm_parameter" "mssql-db-connection" {
  count = var.deploy_retention || var.deploy_product_propensity ? 1 : 0

  name        = "/data-sci/${local.model_name}/db_connection"
  description = "Database Connection details for MSSQL."
  type        = "SecureString"
  value       = "changeme"

  tags = merge({
    "stellar:lifecycle" = "model"
  }, local.tags)

  lifecycle {
    ignore_changes = [
      tags,
      value
    ]
  }

}
