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
      disabled_functions             = ["IngestSharePointFilesTimer"]
      SCM_DO_BUILD_DURING_DEPLOYMENT = "false"
      ENABLE_ORYX_BUILD              = 0
    }
    prod = {
      disabled_functions             = ["IngestSharePointFilesTimer"]
      SCM_DO_BUILD_DURING_DEPLOYMENT = "false"
      ENABLE_ORYX_BUILD              = 0
    }
  }

  function_app_settings = {

  }

  # Dynamically generate disabled function settings
  disabled_function_settings = {
    for func_name in local.function_names :
    "AzureWebJobs.${func_name}.Disabled" => contains(local.base_function_settings[var.environment].disabled_functions, func_name)
  }

  # Extract build settings from base_function_settings
  build_settings = {
    SCM_DO_BUILD_DURING_DEPLOYMENT = local.base_function_settings[var.environment].SCM_DO_BUILD_DURING_DEPLOYMENT
    ENABLE_ORYX_BUILD              = local.base_function_settings[var.environment].ENABLE_ORYX_BUILD
  }

  # Merge base settings with disabled function settings
  all_function_app_settings = merge(local.function_app_settings, local.disabled_function_settings, local.build_settings)


}
