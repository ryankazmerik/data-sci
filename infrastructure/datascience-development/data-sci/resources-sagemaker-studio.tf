resource "aws_sagemaker_domain" "main" {
  count = var.enable_sagemaker_studio ? 1 : 0

  depends_on = [
    module.sagemaker_studio_role
  ]

  domain_name             = "data-sci"
  auth_mode               = "SSO"
  vpc_id                  = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
  subnet_ids              = values(data.terraform_remote_state.account.outputs.vpc_networks["main"].private_subnet_ids["ai"])
  app_network_access_type = "VpcOnly"
  kms_key_id              = data.terraform_remote_state.account.outputs.account_kms_key.arn

  default_user_settings {
    execution_role = module.sagemaker_studio_role[0].iam_role_arn

    security_groups = [
      module.sagemaker_studio_security_group[0].security_group_id
    ]
  }
}