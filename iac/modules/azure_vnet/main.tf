data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}


resource "azurerm_virtual_network" "vnet" {
  name                = "sp-txn-vnet"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  address_space       = ["10.1.0.0/16"]

}

resource "azurerm_subnet" "endpoints_subnet" {
  name                 = "endpoints_snet"
  resource_group_name  = data.azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.1.0.0/24"]


}

resource "azurerm_subnet" "functions_subnet" {
  name                 = "functions_snet"
  resource_group_name  = data.azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.1.1.0/24"]

  delegation {
    name = "delegation-functions"

    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action", "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action"]
    }
  }
}
