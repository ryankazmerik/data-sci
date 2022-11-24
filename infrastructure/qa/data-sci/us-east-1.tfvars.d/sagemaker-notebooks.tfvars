sagemaker_notebooks = {
  "scrites-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 5
    "default_repo"  = "data-sci-toolkit"

    "repos" = [
      "data-sci-template",
      "data-sci-retention",
      "data-sci-product-propensity"
    ]
  }

  "rkazmerik-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 5
    "default_repo"  = "data-sci-retention"

    "repos" = [
      "data-sci-product-propensity",
      "data-sci-toolkit",
      "data-sci"
    ]
  }

  "nrad-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 5
    "default_repo"  = "data-sci"

    "repos" = []
  }

  "jniles-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 5
    "default_repo"  = "data-sci"

    "repos" = []
  }

  "rokoye-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 5
    "default_repo"  = "data-sci"

    "repos" = []
  }

  "yowoseni-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 5
    "default_repo"  = "data-sci"

    "repos" = []
  }
}
