output "vnet_id" {
  description = "ID of the virtual network"
  value       = azurerm_virtual_network.vnet.id
}

output "vnet_name" {
  description = "Name of the virtual network"
  value       = azurerm_virtual_network.vnet.name
}

output "endpoints_subnet_id" {
  description = "ID of endpoints subnet for private endpoints"
  value = azurerm_subnet.endpoints_subnet.id
}

output "functions_subnet_id" {
  description = "ID of the functions subnet for vnet integration"
  value = azurerm_subnet.functions_subnet.id
}