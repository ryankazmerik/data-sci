locals {
  aws_account_id = terraform.workspace == var.workspace ? var.aws_account_id : null

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
      "stellar:lifecycle" = "data-sci",
      "tf_state"          = var.tf_state,
      "tf_workspace"      = var.workspace,
      "owner"             = var.owner,
      "region"            = var.region,
      "environment"       = var.account_name,
      "deployed_by"       = data.aws_caller_identity.current.user_id,
      "updated"           = timestamp()
    },
    var.tags
  )
}
