variable "azurerm_resource_group" {
  description = "Paypal vendor -  ResourceGroup."
  type        = string
  default     = "Paypal-vendor-container-rg"
}

variable "location" {
  description = "Paypal vendor - us vendor - South New Jersey."
  type        = string
  default     = "East US"
}

variable "azurerm_log_analytics_workspace_name" {
  description = "Azure Log Analytics Workspace - Paypal vendor."
  type        = string
  default     = "Paypal-vendor-container-analytic"
}

variable "azurerm_container_app_environment_name" {
  description = "Azure Container App Environment - Paypal vendor."
  type        = string
  default     = "Paypal-vendor-container-environment"
}

variable "azurerm_container_app_name" {
  description = "Azure Container App Paypal vendor."
  type        = string
  default     = "paypalvendorcontainer"
}
