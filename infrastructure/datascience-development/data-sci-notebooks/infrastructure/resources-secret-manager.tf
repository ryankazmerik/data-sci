module "github_secret_manager" {
  count = var.enable_notebook ? 1 : 0

  source = "../../../../../infrastructure-common/modules/secrets_manager_secret"

  secret_name             = "sagemaker-github-login"
  secret_description      = "Login credentials for sagemaker to connect to github."
  kms_key_id              = data.terraform_remote_state.account.outputs.account_kms_key.id
  recovery_window_in_days = 7

  value = var.sagemaker_github_secret

  tags = merge({
    "stellar:lifecycle" = local.product_name
  }, local.tags)
}
