terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.54.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-sp-txn-tf-backend"
    storage_account_name = "sptxntfstr"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {

  }
}

resource "azurerm_resource_group" "rg" {
  name     = local.resource_names.resource_group
  location = "South Africa North"

  tags = {
    Environment         = var.environment
    Department          = "CCoE"
    Application         = var.project_name
    "Application Owner" = var.app_owner
  }
}


module "azure_functions" {
  source                  = "./modules/azure_functions"
  project_name            = var.project_name
  app_owner               = var.app_owner
  resource_group_name     = local.resource_names.resource_group
  location                = var.location
  storage_account_name    = local.resource_names.storage_account
  app_service_plan        = local.resource_names.app_service_plan
  log_analytics_workspace = local.resource_names.log_analytics
  function_app_names      = local.function_app_names
  environment             = var.environment
  alert_contact_name      = var.alert_config[var.environment].contact_name
  alert_contact_email     = var.alert_config[var.environment].contact_email

  depends_on = [azurerm_resource_group.rg, module.azure_kv]

}

module "azure_kv" {
  source              = "./modules/azure_key_vault"
  project_name        = var.project_name
  app_owner           = var.app_owner
  resource_group_name = local.resource_names.resource_group
  location            = var.location
  environment         = var.environment
  kv_name             = local.resource_names.kv_name

  depends_on = [azurerm_resource_group.rg]

}

module "azure_postgre_sql" {
  source              = "./modules/azure_postgresql"
  project_name        = var.project_name
  app_owner           = var.app_owner
  resource_group_name = local.resource_names.resource_group
  location            = var.location
  environment         = var.environment

  depends_on = [azurerm_resource_group.rg]
}
