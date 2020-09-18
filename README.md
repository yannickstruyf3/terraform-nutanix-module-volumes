# Custom Terraform module for Nutanix Volumes

Nutanix volume groups are currently not part of the official Nutanix Terraform provider. I have written a **demo** module to allow integration of the Nutanix Volumes capabilities in Terraform. This module can be used as a workaround since it allows creation and deletion of volume groups and it will also configure the allowed clients. Clients can mount the volumes via in-guest tools.

The repo can be found here:
https://github.com/yannickstruyf3/yst-terraform-nutanix-module-volumes

**Note**: This module is NOT officially supported by Nutanix

The core logic of the module is contained in the `manage_volumes.py` script. This script needs to authenticate with Prism Element. To prevent credentials from appearing in the statefile, these parameters must be passed via environment variables:
- `PE_USERNAME`: Prism Element username
- `PE_PASSWORD`: Prism Element password
- `PE_IP_ADDR`: Prism Element IP

Example: 
```
export PE_IP_ADDR="10.10.1.2"
export PE_USERNAME="my-user"
export PE_PASSWORD="my-password"
```

Module inputs:
- `volume_name`: Name of the volume to be managed
- `volume_size_mb`: Size of the volume
- `storage_container_uuid`: ID of the storage container
- `volume_retain_on_destroy`: Keep the volume and only detach the clients
- `client_addresses`: List of clients that need access to the volume. Format:  "client_addresses":[{ "client_address" : "10.10.10.10" }]


Example module usage:
```
module "yst-volume" {
  source                   = "github.com/yannickstruyf3/yst-terraform-nutanix-module-volumes"
  volume_name              = "my-volume"
  volume_size_mb           = "2048"
  storage_container_uuid   = "0000-0000000-0000000-00000"
  volume_retain_on_destroy = "0"
  client_addresses         = ["10.10.10.10"]
}
```
An example (used with Terraform 0.13) can be found in the `example` folder. This example will provision an Ubuntu VM with multiple volumes attached. Ansible will be used to format the volumes and create a filesystem.
