project_name = "ssptxn"
app_owner    = "AdrianM10"
location     = "South Africa North"

base_config = {
  resource_group   = "rg-sp-txn"
  storage_account  = "aspstr"
  app_service_plan = "asp"
  log_analytics    = "law"
  function_apps    = ["ssptxn-fn-app"]
  kv_name          = "kv-ssp-txn"
}

alert_config = {
  dev = {
    contact_name  = "Dev Support Team"
    contact_email = ""
  }
  prod = {
    contact_name  = "Prod Support Team"
    contact_email = ""
  }
}
