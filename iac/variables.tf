variable "project_name" {
  type        = string
  description = "Name of the project"
}

variable "environment" {
  type        = string
  description = "Environment (dev, prod)"
}

variable "app_owner" {
  type        = string
  description = "Application owner"
}

variable "location" {
  type        = string
  default     = "South Africa North"
  description = "Azure region for resources"
}

variable "base_config" {
  description = "Base configuration for resource naming"
  type = object({
    resource_group   = string
    storage_account  = string
    app_service_plan = string
    log_analytics    = string
    function_apps    = list(string)
  })
}

variable "alert_config" {
  description = "Base configuration for Azure Monitor alert name and email"
  type = object({
    dev = object({
      contact_name  = string
      contact_email = string
    })
    prod = object({
      contact_name  = string
      contact_email = string
    })
  })

}

variable "kv_name_base" {
  type = string
  description = "Base name for Azure Key Vault"
  sensitive = true
}
