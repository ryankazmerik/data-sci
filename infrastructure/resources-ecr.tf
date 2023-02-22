module "dw_ecr_repository_retention" {
  count = var.deploy_retention || var.deploy_product_propensity ? 1 : 0

  source          = "../../infrastructure-common/modules/ecr_repository"
  repository_name = "${local.model_name}-retention"
  scan_on_push    = true
  tags            = local.tags
}

module "dw_ecr_repository_product_propensity" {
  count = var.deploy_retention || var.deploy_product_propensity ? 1 : 0

  source          = "../../infrastructure-common/modules/ecr_repository"
  repository_name = "${local.model_name}-product-propensity"
  scan_on_push    = true
  tags            = local.tags
}

module "dw_ecr_repository_sagemaker_kernel" {
  count = var.deploy_sagemaker_image ? 1 : 0

  source          = "../../infrastructure-common/modules/ecr_repository"
  repository_name = "data-sci-sagemaker-custom-kernel"
  scan_on_push    = true
  tags            = local.tags
}
