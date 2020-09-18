locals {
  ansible_extra_vars = {
    "target_host" : "${nutanix_virtual_machine.vm.nic_list[0].ip_endpoint_list[0].ip}",
    "iscsi_target" : "${var.pe_data_services_ip}"
    "disk_mapping" : var.disk_mapping
  }
}

resource "null_resource" "run_ansible" {
  depends_on = [nutanix_virtual_machine.vm, module.yst-volume]
  triggers = {
    command = "${timestamp()}"
  }
  # Create-time provisioner
  provisioner "local-exec" {
    environment = {
      ANSIBLE_REMOTE_USER = var.ansible_user
    }
    command = "ansible-playbook -i '${nutanix_virtual_machine.vm.nic_list[0].ip_endpoint_list[0].ip},' format_scsci_volume.yaml --extra-vars='${jsonencode(local.ansible_extra_vars)}'"
  }
}
