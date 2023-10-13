terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "3.75.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "resource_group" {
  name     = var.azurerm_resource_group
  location = var.location
}

resource "azurerm_log_analytics_workspace" "analytics_workspace" {
  name                = var.azurerm_log_analytics_workspace_name
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "app_environment" {
  name                       = var.azurerm_container_app_environment_name
  location                   = azurerm_resource_group.resource_group.location
  resource_group_name        = azurerm_resource_group.resource_group.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.analytics_workspace.id
}
resource "azurerm_container_app" "app" {
  name                         = var.azurerm_container_app_name
  container_app_environment_id = azurerm_container_app_environment.app_environment.id
  resource_group_name          = azurerm_resource_group.resource_group.name
  revision_mode                = "Multiple"
  template {
    container {
      name   = "refinaryapp"
      image  = "nginxdemos/hello"
      cpu    = 0.5
      memory = "1Gi"
    }
  }
  ingress {
     allow_insecure_connections = false
     target_port = 80
     traffic_weight {
      percentage = 100
     }
     external_enabled = true
   }
}

output "azurerm_container_app_url" {
  value = azurerm_container_app.app.latest_revision_fqdn
}

output "azurerm_container_app_revision_name" {
  value = azurerm_container_app.app.latest_revision_name
  
}
