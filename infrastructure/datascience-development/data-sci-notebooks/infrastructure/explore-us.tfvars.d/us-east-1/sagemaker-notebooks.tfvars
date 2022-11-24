sagemaker_notebooks = {
  "scrites-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 10
    "default_repo"  = "data-sci-toolkit"

    "repos" = [
      "data-sci-template",
      "data-sci-retention",
      "data-sci-product-propensity"
    ]
  }

  "rkazmerik-notebook" = {
    "instance_type" = "ml.m5.xlarge"
    "volume_size"   = 50
    "default_repo"  = "data-sci-event-propensity"

    "repos" = [
      "data-sci-product-propensity",
      "data-sci-toolkit",
      "data-sci-retention"
    ]
  }

  "jniles-notebook" = {
    "instance_type" = "ml.c4.8xlarge"
    "volume_size"   = 50
    "default_repo"  = "data-sci-event-propensity"

    "repos" = [
      "data-sci"
    ]
  }

  "lschmold-dev-notebook" = {
    "instance_type" = "ml.t3.medium"
    "volume_size"   = 10
    "default_repo"  = "customer-innovation"

    "repos" = []
  }

  "pmorrison-prod-notebook" = {
    "instance_type" = "ml.c4.4xlarge"
    "volume_size"   = 20
    "default_repo"  = "data-sci"

    "repos" = [
      "data-sci-product-propensity",
      "data-sci-toolkit"
    ]
  }

  "gdonst-prod-notebook" = {
    "instance_type" = "ml.m5.xlarge"
    "volume_size"   = 20
    "default_repo"  = "data-sci-retention"

    "repos" = [
      "data-sci-product-propensity",
      "data-sci-event-propensity",
      "data-sci-toolkit"
    ]
  }
}
