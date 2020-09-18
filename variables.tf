variable "volume_name" {
  type = string
}

variable "volume_size_mb" {
  type = string
}

variable "storage_container_uuid" {
  type = string
}

variable "volume_retain_on_destroy" {
}

variable "client_addresses" {
  type = list
}
