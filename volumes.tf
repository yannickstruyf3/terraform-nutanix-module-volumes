resource "null_resource" "create_volume" {
  triggers = {
    ips = jsonencode(var.client_addresses),
    dm = jsonencode({
      "volume_name" : var.volume_name
      "volume_size_mb" : var.volume_size_mb
      "storage_container_uuid" : var.storage_container_uuid
      "volume_retain_on_destroy" : var.volume_retain_on_destroy
    })
  }
  # Create-time provisioner
  provisioner "local-exec" {
    command = "python3 ${path.module}/manage_volumes.py create '${jsonencode(merge(jsondecode(self.triggers.dm), { client_addresses = [for i in jsondecode(self.triggers.ips) : { client_address : i }] }))}'"
  }
}
# Destroy-time provisioner
resource "null_resource" "delete_volume" {
  triggers = {
    dm = jsonencode({
      "volume_name" : var.volume_name
      "volume_size_mb" : var.volume_size_mb
      "storage_container_uuid" : var.storage_container_uuid
      "volume_retain_on_destroy" : var.volume_retain_on_destroy
    })
  }
  provisioner "local-exec" {
    when    = destroy
    command = "python3 ${path.module}/manage_volumes.py delete '${self.triggers.dm}'"
  }
}
