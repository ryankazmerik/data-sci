# module "sagemaker_image_ecr_repositories" {
#   for_each = var.enable_sagemaker_studio && length(var.sagemaker_image_repos) > 0 ? var.sagemaker_image_repos : {}

#   source          = "../../../../infrastructure-common/modules/ecr_repository"
#   repository_name = "${each.key}-sagemaker-image"
#   scan_on_push    = true
#   tags            = local.tags
# }
