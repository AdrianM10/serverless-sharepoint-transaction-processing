variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Name of the location"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string

}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "app_owner" {
  description = "Application owner"
  type        = string
}

variable "kv_name" {
  description = "Name of Azure Key Vault"
  type        = string
}

variable "key_vault_secret_officers" {
  type    = list(string)
  default = []
}
