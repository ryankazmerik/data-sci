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

module "sagemaker_studio_security_group" {
  count = var.enable_sagemaker_studio ? 1 : 0
  
  source            = "../../../../infrastructure-common/modules/vpc_security_group"
  vpc_id            = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
  group_name        = "sagemaker-studio-sg"
  group_description = "Controls traffic to/from the sagemaker studio."

  ingress_rules_map = {
    all_sagemaker_endpoints = {
      security_group_id = "sg-00a136e479e82f2ac"
      description       = "All sagemaker endpoints ingress rule."
      from_port         = 0
      to_port           = 65535
      protocol          = "tcp"
    }

    self = {
      description = "Self Reference"
      from_port   = 0
      to_port     = 65535
      protocol    = -1
      self        = true
    }
  }

  egress_rules = local.default_security_group_egress_rules

  tags = merge(
    {
      "Name" = "sagemaker-studio-sg"
    },
    local.tags
  )
}

# module "self_referenced_security_group" {
#   source            = "../../infrastructure-common/modules/vpc_security_group"
#   vpc_id            = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
#   group_name        = "self-reference-sg"
#   group_description = "Controls traffic to/from itself."

#   ingress_rules_map = {
#     self = {
#       description = "Self Reference"
#       from_port   = 0
#       to_port     = 65535
#       protocol    = "tcp"
#       self        = true
#     }
#   }

#   egress_rules = local.default_security_group_egress_rules

#   tags = merge(
#     {
#       "Name" = "${var.environment}-self-reference-sg"
#     },
#     local.tags
#   )
# }
