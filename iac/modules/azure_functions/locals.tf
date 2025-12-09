locals {

  # Environment suffixes
  env_suffixes = {
    dev  = "dev"
    prod = "prod"
  }

  function_app_name = "ssptxn-fn-app-${local.env_suffixes[var.environment]}"
  function_names    = ["IngestBankTransactions"]

  base_function_settings = {
    dev = {
      disabled_functions = []
    }
    prod = {
      disabled_functions = []
    }
  }

  function_app_settings = {

  }

  # Dynamically generate disabled function settings
  disabled_function_settings = {
    for func_name in local.function_names :
    "AzureWebJobs.${func_name}.Disabled" => contains(local.base_function_settings[var.environment].disabled_functions, func_name)
  }

  # Merge base settings with disabled function settings
  all_function_app_settings = merge(local.function_app_settings, local.disabled_function_settings)


}
