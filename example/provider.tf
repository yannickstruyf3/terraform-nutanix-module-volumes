provider "nutanix" {
  username = var.pc_username
  password = var.pc_password
  endpoint = var.pc_ip
  insecure = true
  port     = 9440
  wait_timeout = 2
}

