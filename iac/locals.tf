locals {
  env_suffix = {
    dev  = "dev"
    prod = "prod"
  }

  base_names = {
    resource_group   = var.base_config.resource_group
    storage_account  = var.base_config.storage_account
    app_service_plan = var.base_config.app_service_plan
    log_analytics    = var.base_config.log_analytics
    kv_name          = var.base_config.kv_name
  }

  # Function app configurations
  function_apps = {
    for app in var.base_config.function_apps : app => {
      name = app
      path = "${var.project_name}-${app}"
    }
  }

  # Generate resource names
  resource_names = {
    resource_group   = "${local.base_names.resource_group}-${local.env_suffix[var.environment]}"
    storage_account  = "${lower(var.project_name)}${local.base_names.storage_account}${local.env_suffix[var.environment]}"
    app_service_plan = "${var.project_name}-${local.base_names.app_service_plan}-${local.env_suffix[var.environment]}"
    log_analytics    = "${local.base_names.log_analytics}-${var.project_name}-${local.env_suffix[var.environment]}"
    kv_name          = "kv-ssp-txn-${local.env_suffix[var.environment]}-01"
  }

  # Generate function app names
  function_app_names = [
    for app in var.base_config.function_apps :
    # "${var.project_name}-${app}-${local.env_suffix[var.environment]}"
    "${app}-${local.env_suffix[var.environment]}"
  ]
}
