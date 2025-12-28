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
  sensitive = true

}

variable "kv_name" {
  type        = string
  description = "Azure Key Vault name"
  sensitive   = true
}

variable "ip_address" {
  description = "IP Address for Firewall rule"
  type        = string
  sensitive   = true
}

variable "psql_server_name" {
  description = "Postgre SQL Server name"
  type        = string
  sensitive   = true
}

variable "psql_admin_sg_object_id" {
  description = "Postgre SQL admin Entra security group"
  type        = string
  sensitive   = true
}

variable "vault_url_dev" {
  description = "Azure Key Vault URL"
  type        = string
  sensitive   = true
}

variable "db_host" {
  description = "DB Host Endpoint"
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Azure Tenant ID"
  type = string
  sensitive = true
}