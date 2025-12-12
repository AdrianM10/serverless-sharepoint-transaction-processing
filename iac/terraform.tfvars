project_name = "sptxn"
app_owner    = "M10"
location     = "South Africa North"

base_config = {
  resource_group   = "rg-sp-txn"
  storage_account  = "aspstr"
  app_service_plan = "asp"
  log_analytics    = "law"
  function_apps    = ["sptxn-fn-app"]
}

alert_config = {
  dev = {
    contact_name  = "Dev Support Team"
    contact_email = "a63470453@gmail.com"
  }
  prod = {
    contact_name  = "Prod Support Team"
    contact_email = "a63470453@gmail.com"
  }
}
