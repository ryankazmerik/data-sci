module "dw_ecr_repository_retention" {
  count = var.deploy_retention || var.deploy_product_propensity ? 1 : 0

  source          = "../../infrastructure-common/modules/ecr_repository"
  repository_name = "${local.model_name}-retention"
  scan_on_push    = true
  tags            = local.tags
}
