output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "vm_public_ip" {
  value = azurerm_public_ip.this.ip_address
}

output "vm_admin_username" {
  value = azurerm_linux_virtual_machine.this.admin_username
}

output "telemetry_url" {
  value = "http://${azurerm_public_ip.this.ip_address}:${var.telemetry_public_port}"
}
