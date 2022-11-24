locals {
  aws_account_id = terraform.workspace == var.workspace ? var.aws_account_id : null

  experiments_bucket_name = var.enable_sagemaker_notebooks ? "data-sci-experiments-${random_string.random_bucket_id[0].result}" : null

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
      maintained_by                         = "terraform"
      environment                           = var.environment
      deployed_by                           = split("/", data.aws_caller_identity.origin.arn)[2]
      tf_state                              = var.tf_state
      tf_workspace                          = var.workspace
      owner                                 = var.owner
    },
    var.tags
  )
}
