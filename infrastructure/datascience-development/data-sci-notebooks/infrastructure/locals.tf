locals {
  aws_account_id = terraform.workspace == var.workspace ? var.aws_account_id : null

  product_name = "ai"

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
      "updated"     = timestamp()
    },
    var.tags
  )
}
