data "azurerm_resource_group" "rg" {
  name = var.resource_group_name

}

data "azurerm_client_config" "current" {}

resource "azurerm_postgresql_flexible_server" "psql_server" {
  name                = var.psql_server_name
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  version             = "18"
  storage_mb          = 32768
  sku_name            = "B_Standard_B1ms"
  zone                = 2

  authentication {
    password_auth_enabled         = false
    active_directory_auth_enabled = true
  }

}

resource "azurerm_postgresql_flexible_server_database" "psql_db" {
  name      = "transactions"
  server_id = azurerm_postgresql_flexible_server.psql_server.id
  collation = "en_US.utf8"
  charset   = "UTF8"

  # prevent the possibility of accidental data loss
  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_postgresql_flexible_server_active_directory_administrator" "psql_admin" {
  server_name         = azurerm_postgresql_flexible_server.psql_server.name
  resource_group_name = data.azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  object_id           = var.psql_admin_sg_object_id
  principal_name      = "POSTGRE_SQL_ADMINS"
  principal_type      = "Group"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "psql_fw_rule" {
  name             = "client-ip"
  server_id        = azurerm_postgresql_flexible_server.psql_server.id
  start_ip_address = var.ip_address
  end_ip_address   = var.ip_address
}

resource "azurerm_private_dns_zone" "psql_dns_zone" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = data.azurerm_resource_group.rg.name

}

resource "azurerm_private_dns_zone_virtual_network_link" "pvt_dns_zone_link" {
  name                  = "dns_zone_link"
  resource_group_name   = data.azurerm_resource_group.rg.name
  private_dns_zone_name = azurerm_private_dns_zone.psql_dns_zone.name
  virtual_network_id    = var.vnet_id
}

resource "azurerm_private_endpoint" "postgres_pe" {
  name                = "sp-txn-postgres-sql-pe"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  subnet_id           = var.endpoints_subnet_id

  private_service_connection {
    name                           = "pvt-svc-postgres"
    private_connection_resource_id = azurerm_postgresql_flexible_server.psql_server.id
    is_manual_connection           = false
    subresource_names              = ["postgresqlServer"]
  }

  private_dns_zone_group {
    name                 = "postgres-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.psql_dns_zone.id]
  }

}
