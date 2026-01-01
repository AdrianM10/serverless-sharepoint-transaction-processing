locals {

  # Environment suffixes
  env_suffixes = {
    dev  = "dev"
    prod = "prod"
  }

  function_app_name = "sptxn-fn-app-${local.env_suffixes[var.environment]}"
  function_names    = ["IngestSharePointFilesTimer"]

  base_function_settings = {
    dev = {
      disabled_functions = []
      vault_url          = var.vault_url_dev
      db_host            = var.db_host
      environment        = "azure-dev"
    }
    prod = {
      disabled_functions = ["IngestSharePointFilesTimer"]
      vault_url          = ""
      db_host            = ""
      environment        = "azure-prod"
    }
  }

  function_app_settings = {
    vault_url   = local.base_function_settings[var.environment].vault_url
    DB_HOST     = local.base_function_settings[var.environment].db_host
    environment = local.base_function_settings[var.environment].environment
  }

  # Dynamically generate disabled function settings
  disabled_function_settings = {
    for func_name in local.function_names :
    "AzureWebJobs.${func_name}.Disabled" => contains(local.base_function_settings[var.environment].disabled_functions, func_name)
  }

  # Merge base settings with disabled function settings
  all_function_app_settings = merge(local.function_app_settings, local.disabled_function_settings)

}
