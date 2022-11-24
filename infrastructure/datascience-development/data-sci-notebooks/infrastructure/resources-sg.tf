module "sagemaker_notebook_security_group" {
  source            = "../../../../../infrastructure-common/modules/vpc_security_group"
  vpc_id            = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
  group_name        = "sagemaker-notebook-sg"
  group_description = "Controls traffic to/from the sagemaker notebooks."

  ingress_rules_map = {
  }
  egress_rules = local.default_security_group_egress_rules

  tags = merge(
    {
      "Name" = "${var.environment}-sagemaker-notebook-sg"
    },
    local.tags
  )
}
