module "sagemaker_code_repositories" {
  for_each = var.enable_notebook ? var.sagemaker_git_repos : {}

  depends_on = [module.github_secret_manager]

  source               = "../../../../../infrastructure-common/modules/sagemaker_code_repository"
  code_repository_name = each.key

  git_config = {
    repository_url = each.value.git_url
    branch         = each.value.branch
    secret_arn     = module.github_secret_manager[0].secrets_manager_secret_arn
  }
}

module "sagemaker_notebook_lifecycle_default" {
  count = var.enable_notebook ? 1 : 0

  depends_on = [
    module.sagemaker_code_repositories
  ]

  source         = "../../../../../infrastructure-common/modules/sagemaker_notebook_lifecycle"
  lifecycle_name = "${local.product_name}-notebook-lifecycle-default"
  on_start       = file("${path.module}/../src/scripts/start_notebook.sh")
}

module "sagemaker_notebook_lifecycle_backup_ebs" {
  count = var.enable_notebook ? 1 : 0

  depends_on = [
    module.sagemaker_code_repositories
  ]

  source         = "../../../../../infrastructure-common/modules/sagemaker_notebook_lifecycle"
  lifecycle_name = "${local.product_name}-notebook-lifecycle-backup-ebs"
  on_start       = file("${path.module}/../src/scripts/backup_ebs_on_start.sh")
}

module "sagemaker_notebook_instances" {
  for_each = var.enable_notebook && length(var.sagemaker_notebooks) > 0 ? var.sagemaker_notebooks : {}

  depends_on = [
    module.sagemaker_code_repositories,
    module.sagemaker_notebook_security_group,
    module.sagemaker_notebook_lifecycle_default,
    module.iam_role_notebook_instance
  ]

  source                = "../../../../../infrastructure-common/modules/sagemaker_notebook_instance"
  role_arn              = module.iam_role_notebook_instance[0].iam_role_arn
  lifecycle_config_name = module.sagemaker_notebook_lifecycle_default[0].configuration_name
  instance_name         = each.key
  instance_type         = each.value.instance_type
  volume_size           = each.value.volume_size

  subnet_id       = [for key, value in data.terraform_remote_state.account.outputs.vpc_networks["main"].private_subnet_ids["ai"] : value][0]
  security_groups = [module.sagemaker_notebook_security_group.security_group_id, data.terraform_remote_state.account.outputs.vpc_networks["main"].security_group_ids["legacy_prod_sql"]]

  kms_key_id             = data.terraform_remote_state.account.outputs.account_kms_key.id
  root_access            = true
  direct_internet_access = false

  default_code_repository = module.sagemaker_code_repositories[each.value.default_repo].repository_id

  additional_code_repositories = each.value.repos
}
