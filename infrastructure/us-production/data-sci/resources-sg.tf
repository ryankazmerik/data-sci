module "sagemaker_training_sg" {
  source            = "../../../../infrastructure-common/modules/vpc_security_group"
  vpc_id            = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
  group_name        = "sagemaker-training-sg-${random_string.random_sg_id.result}"
  group_description = "Controls inter-container traffic encryption for UDP 500 and Protocol 50."

  ingress_rules_map = {
    udp500 = {
      description = "Sagemaker Training UDP500"
      from_port   = 500
      to_port     = 500
      protocol    = "udp"
      self        = true
    }
    esp50 = {
      description = "Sagemaker Training ESP50"
      from_port   = -1
      to_port     = -1
      protocol    = "50"
      self        = true
    }
  }

  egress_rules = local.default_security_group_egress_rules

  tags = merge(
    {
      "Name" = "sagemaker-training-sg-${random_string.random_sg_id.result}"
    },
    local.tags
  )
}

module "sagemaker_studio_sg" {
  count = var.enable_sagemaker_studio ? 1 : 0

  source            = "../../../../infrastructure-common/modules/vpc_security_group"
  vpc_id            = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
  group_name        = "sagemaker-studio-sg"
  group_description = "Controls traffic to/from the sagemaker studio."

  ingress_rules_map = {}

  egress_rules = local.default_security_group_egress_rules

  tags = merge(
    {
      "Name" = "${var.environment}-sagemaker-studio-sg"
    },
    local.tags
  )
}