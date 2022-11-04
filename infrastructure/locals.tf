locals {
  aws_account_id = terraform.workspace == var.workspace ? var.aws_account_id : null

  model_name = "data-sci-dw"

  pipelines = ["product-propensity", "retention"]

  # model_bucket_name   = format("%s-model-%s-%s-%s", var.account_name, local.model_name, var.region, random_string.random_bucket_id.result)
  # config_bucket_name  = format("%s-config-%s-%s-%s", var.account_name, local.model_name, var.region, random_string.random_bucket_id.result)
  # curated_bucket_name = format("%s-curated-%s-%s-%s", var.account_name, local.model_name, var.region, random_string.random_bucket_id.result)

  all_endpoints_ingress_rule = {
    security_group_id = data.terraform_remote_state.account.outputs.vpc_networks["main"]["security_group_ids"]["all_endpoints"]
    description       = "All endpoints ingress rule."
    from_port         = 0
    to_port           = 65535
    protocol          = "tcp"
  }

  default_security_group_egress_rules = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]

  tags = merge(
    {
      "environment" = var.environment,
      "deployed_by" = data.aws_caller_identity.current.user_id,
      "model"       = local.model_name
    },
    var.tags
  )
}
