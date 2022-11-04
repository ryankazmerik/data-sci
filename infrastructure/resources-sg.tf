module "dw_lambda_sg" {
  count = var.deploy_retention || var.deploy_product_propensity ? 1 : 0

  source            = "../../infrastructure-common/modules/vpc_security_group"
  vpc_id            = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
  group_name        = "${var.account_name}-${local.model_name}"
  group_description = "Controls network access for the data-sci retention lambda functions."

  ingress_rules_map = {
    all_endpoints = local.all_endpoints_ingress_rule
  }

  egress_rules = local.default_security_group_egress_rules

  tags = local.tags
}
