variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Name of the location"
  type        = string
}

variable "storage_account_name" {
  description = "Name of the storage account used by the App Service Plan"
  type        = string

}

variable "app_service_plan" {
  description = "Name of the App Service Plan"
  type        = string

}

variable "function_app_names" {
  description = "Name(s) of the function apps"
  type        = list(string)
}

variable "log_analytics_workspace" {
  description = "Name of the log analytics workspace"
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

variable "alert_contact_name" {
  description = "Name of the alert contact"
  type        = string
}

variable "alert_contact_email" {
  description = "Email address for alert notifications"
  type        = string

}
