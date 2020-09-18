# #Generate cloud-init config
data "template_file" "cloud-init" {
  template = "${file("cloud-init.tpl")}"
  vars = {
    vmname = var.vmname
  }
}

data "nutanix_cluster" "cluster" {
  name = var.cluster_name
}

data "nutanix_image" "ubuntu" {
  image_name = var.image_name
}

data "nutanix_subnet" "vlan" {
  subnet_name = var.subnet_name
}

resource "nutanix_virtual_machine" "vm" {
  name                 = var.vmname
  cluster_uuid         = data.nutanix_cluster.cluster.id
  num_vcpus_per_socket = "2"
  num_sockets          = "1"
  memory_size_mib      = 2048
  disk_list {
    data_source_reference = {
      kind = "image"
      uuid = data.nutanix_image.ubuntu.id
    }
    disk_size_bytes = 30 * 1024 * 1024 * 1024
  }
  guest_customization_cloud_init_user_data = base64encode(data.template_file.cloud-init.rendered)

  nic_list {
    subnet_uuid = data.nutanix_subnet.vlan.id
  }
  serial_port_list {
    index        = 1
    is_connected = true
  }
}

module "yst-volume" {
  source                   = "github.com/yannickstruyf3/yst-terraform-nutanix-module-volumes"
  depends_on               = [nutanix_virtual_machine.vm]
  count                    = length(var.disk_mapping)
  volume_name              = var.disk_mapping[count.index].volume_name
  volume_size_mb           = var.disk_mapping[count.index].volume_size_mb
  storage_container_uuid   = var.disk_mapping[count.index].storage_container_uuid
  volume_retain_on_destroy = var.disk_mapping[count.index].volume_retain_on_destroy
  client_addresses         = [nutanix_virtual_machine.vm.nic_list[0].ip_endpoint_list[0].ip]
}

output "connect" {
  value = "VM provisioned with IP: ${nutanix_virtual_machine.vm.nic_list[0].ip_endpoint_list[0].ip}"
}

