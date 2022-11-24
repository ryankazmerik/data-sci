resource "aws_sagemaker_domain" "main" {
  count = var.enable_sagemaker_studio ? 1 : 0

  depends_on = [
    module.sagemaker_studio_default_role,
    module.sagemaker_studio_sg
  ]

  domain_name             = "${var.environment}-sagemaker-domain"
  auth_mode               = "SSO"
  vpc_id                  = data.terraform_remote_state.account.outputs.vpc_networks["main"].vpc_id
  subnet_ids              = values(data.terraform_remote_state.account.outputs.vpc_networks["main"].private_subnet_ids["ai"])
  app_network_access_type = "VpcOnly"
  kms_key_id              = data.terraform_remote_state.account.outputs.account_kms_key.arn

  default_user_settings {
    execution_role = module.sagemaker_studio_default_role[0].iam_role_arn

    security_groups = [
      data.terraform_remote_state.account.outputs.vpc_networks["main"].security_group_ids["all_endpoints"],
      module.sagemaker_studio_sg[0].security_group_id
    ]


    # kernel_gateway_app_settings {
    #   custom_image {
    #     app_image_config_name = aws_sagemaker_app_image_config.test[0].app_image_config_name
    #     image_name            = "ryan-custom"
    #     image_version_number  = 1
    #   }
    # }
  }
}

resource "aws_sagemaker_user_profile" "sagemaker_user_profiles" {
  for_each = var.enable_sagemaker_studio && length(var.sagemaker_user_profiles) > 0 ? var.sagemaker_user_profiles : {}

  depends_on = [
    aws_sagemaker_domain.main
  ]

  domain_id                      = aws_sagemaker_domain.main[0].id
  user_profile_name              = each.key
  single_sign_on_user_value      = each.value.email
  single_sign_on_user_identifier = "UserName"

  user_settings {
    execution_role  = module.sagemaker_studio_default_role[0].iam_role_arn
    security_groups = []

    sharing_settings {
      notebook_output_option = "Disabled"
    }

    # tensor_board_app_settings {
    #     default_resource_spec {
    #         instance_type = ""
    #         sagemaker_image_arn = ""
    #     }
    # }

    # jupyter_server_app_settings {
    #     default_resource_spec {
    #         instance_type = "ml.t3.medium"
    #         sagemaker_image_arn = ""
    #     }
    # }

    # kernel_gateway_app_settings {
    #     default_resource_spec {
    #         instance_type = ""
    #         sagemaker_image_arn = ""
    #     }
    # }
  }

  tags = local.tags
}


# resource "aws_sagemaker_app" "default_app" {
#     for_each = var.enable_studio && length(var.sagemaker_user_profiles) > 0 ? var.sagemaker_user_profiles : {}

#   depends_on = [
#     aws_sagemaker_domain.main
#   ]
#   domain_id         = aws_sagemaker_domain.main[0].id
#   user_profile_name = each.key
#   app_name          = "default"
#   app_type          = "JupyterServer"
#   resource_spec {

#   }
#   tags = {}
# }

# resource "aws_sagemaker_image" "sagemaker_images" {
#   for_each = var.enable_studio && length(var.sagemaker_image_repos) > 0 ? var.sagemaker_image_repos : {}

#   depends_on = [
#     module.sagemaker_image_role
#   ]

#   image_name   = each.key
#   role_arn     = module.sagemaker_image_role[0].iam_role_arn
#   display_name = each.key
#   description  = each.value.description
#   tags         = {}
# }

# resource "aws_sagemaker_image_version" "sagemaker_image_versions" {
#   for_each   = var.enable_studio && length(var.sagemaker_image_repos) > 0 ? var.sagemaker_image_repos : {}
#   image_name = aws_sagemaker_image.sagemaker_images[each.key].id
#   base_image = "base-image"
# }

# resource "aws_sagemaker_app_image_config" "test" {
#   count = var.enable_studio ? 1 : 0

#   app_image_config_name = "example"

#   kernel_gateway_image_config {
#     kernel_spec {
#       name = "example"
#     }

#     file_system_config {}
#   }
# }