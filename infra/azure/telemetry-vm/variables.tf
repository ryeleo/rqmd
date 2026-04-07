variable "subscription_id" {
  type        = string
  description = "Azure subscription ID"
}

variable "location" {
  type        = string
  default     = "westus2"
  description = "Azure region"
}

variable "resource_group_name" {
  type        = string
  default     = "rqmd-telemetry-vm-rg"
  description = "Resource group name"
}

variable "prefix" {
  type        = string
  default     = "rqmdtelemetry"
  description = "Name prefix for Azure resources"
}

variable "vm_size" {
  type        = string
  default     = "Standard_B2s"
  description = "VM size for telemetry stack"
}

variable "os_disk_size_gb" {
  type        = number
  default     = 64
  description = "OS disk size in GB"
}

variable "vm_admin_username" {
  type        = string
  default     = "azureuser"
  description = "Linux VM admin username"
}

variable "vm_admin_ssh_public_key" {
  type        = string
  sensitive   = true
  description = "SSH public key for VM access"
}

variable "allowed_ssh_cidr" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR allowed for SSH. Tighten this in production."
}

variable "telemetry_public_port" {
  type        = string
  default     = "18080"
  description = "Public telemetry API port exposed by the VM"
}
