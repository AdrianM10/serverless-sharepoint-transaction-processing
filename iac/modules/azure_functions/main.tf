data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

}

resource "azurerm_storage_container" "container" {
  name                  = "ssptxn-flexcontainer"
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
}

resource "azurerm_log_analytics_workspace" "law" {
  name                = var.log_analytics_workspace
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

}

resource "azurerm_service_plan" "appserviceplan" {
  name                = var.app_service_plan
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku_name            = "FC1"
  os_type             = "Linux"
}

resource "azurerm_function_app_flex_consumption" "functionpp" {
  count               = length(var.function_app_names)
  name                = "sptxn-fn-app-${var.environment}"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.appserviceplan.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.storage.primary_blob_endpoint}${azurerm_storage_container.container.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.storage.primary_access_key
  runtime_name                = "python"
  runtime_version             = "3.12"
  maximum_instance_count      = 40
  instance_memory_in_mb       = 2048

  app_settings = local.function_app_settings[var.function_app_names[count.index]]

  https_only = true

  site_config {
    minimum_tls_version      = "1.3"
    application_insights_key = azurerm_application_insights.app_insights[count.index].instrumentation_key
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_application_insights" "app_insights" {
  name                = "sptxn-fn-app-${var.environment}-app-insights"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"

}

resource "azurerm_monitor_action_group" "function_alerts" {
  name                = "ag-${var.project_name}-${var.environment}"
  resource_group_name = data.azurerm_resource_group.rg.name
  short_name          = var.project_name

  depends_on = [data.azurerm_resource_group.rg]

  email_receiver {
    name                    = var.alert_contact_name
    email_address           = var.alert_contact_email
    use_common_alert_schema = true
  }

  tags = {
    Environment = var.environment
  }
}


resource "azurerm_monitor_scheduled_query_rules_alert_v2" "function_alert_query" {
  name                = "sptxn-fn-app-${var.environment}-alert-rule"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location


  evaluation_frequency = "PT5M"
  window_duration      = "PT5M"
  scopes               = [azurerm_application_insights.app_insights.id]
  severity             = 3

  criteria {
    query = <<-QUERY
    traces
    | where severityLevel == 3
    | where timestamp >= ago(5m)
    | where message !contains "Failed to publish status to /memoryactivity"
    | where message !contains "Failed to publish status to /functionactivity"
    | where message !contains "Temporary failure in name resolution"
    | where message !contains "Singleton lock renewal failed for blob"
  QUERY

    time_aggregation_method = "Count"
    threshold               = 0
    operator                = "GreaterThan"
  }


  action {
    action_groups = [azurerm_monitor_action_group.function_alerts.id]
  }

  display_name = "sptxn-fn-app-${var.environment}-alert-rule"
  description  = "The backend function app(s) for ${var.project_name} has encountered an error. Please contact ${var.app_owner}"
  enabled      = true

}

data "azurerm_key_vault" "kv" {
  name                = "kv-ssp-txn-dev-01"
  resource_group_name = data.azurerm_resource_group.rg.name
}

resource "azurerm_role_assignment" "kv_secrets_user" {
  count                = length(var.function_app_names)
  scope                = data.azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_function_app_flex_consumption.functionpp[count.index].identity[0].principal_id

}
