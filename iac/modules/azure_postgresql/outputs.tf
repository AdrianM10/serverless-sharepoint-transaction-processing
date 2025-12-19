output "fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.psql_server.fqdn
  sensitive   = true
}

output "server_id" {
  description = "PostgreSQL server ID"
  value       = azurerm_postgresql_flexible_server.psql_server.id

}

output "private_endpoint_ip" {
  description = "Private IP address of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.psql_server.private_service_connection[0].private_ip_address
  sensitive   = true
}
