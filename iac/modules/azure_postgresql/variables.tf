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
  type = string
  sensitive = true
}
