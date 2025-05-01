# linux-dns-server-provisioner

A cross-platform script for automated DNS server deployment and management on Linux systems.

## Overview

Linux DNS Server Provisioner is a powerful tool designed to simplify the deployment, configuration, and management of BIND DNS servers on various Linux distributions. It automates the entire process from installation to configuration, making it accessible for system administrators of all experience levels.

The script provides an interactive, color-coded interface that guides you through the setup process, handles distribution-specific configurations, and performs validation at each step to ensure a properly functioning DNS server.

---

## Features

### Cross-Distribution Support

- **Debian-based:** Ubuntu, Debian, Linux Mint  
- **RHEL-based:** Rocky Linux, CentOS, RHEL, AlmaLinux, Fedora  
- Automatic distribution detection with fallback options

### Comprehensive DNS Setup

- BIND9/named installation and configuration
- Forward and reverse zone creation
- SOA, NS, A, and PTR record management
- DNS forwarders configuration

### Network Management

- Static IP configuration via Netplan (Debian) or NetworkManager (RHEL)
- Network interface detection and selection
- Hostname configuration
- Gateway and subnet configuration
- Automatic backup of existing network configurations

### Security Features

- Firewall configuration (UFW or firewalld)
- SELinux context configuration for RHEL-based systems
- Proper file permissions for zone files

### Validation and Testing

- Configuration syntax checking
- Forward and reverse lookup testing
- Service status verification

### Uninstallation and Cleanup

- Complete DNS server removal
- Network configuration restoration
- Hostname reset options
- Configuration file cleanup

### User Experience

- Color-coded output for better readability
- Detailed progress information
- Error handling with recovery options
- Backup and restore functionality

---

## System Requirements

- Linux OS (Debian-based or RHEL-based)
- Root/sudo privileges
- Internet connection (for package installation)
- Python 3.6+

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/Linux-DNS-Server-Provisioner.git
cd Linux-DNS-Server-Provisioner
```

2. Make the script executable:

```bash
chmod +x linux_dns_server_provisioner.py
```

---

## Usage

### Installing a DNS Server

Run the script with root privileges:

```bash
sudo ./linux_dns_server_provisioner.py
```

The script will:

1. Detect your Linux distribution  
2. Prompt for network configuration  
3. Install necessary packages  
4. Configure DNS zones  
5. Set up firewall rules  
6. Verify the installation  

### Uninstalling a DNS Server

To uninstall or reconfigure:

```bash
sudo ./linux_dns_server_provisioner.py
```

Uninstallation includes:

- Stops/disables DNS service
- Removes DNS packages
- Restores original network configuration
- Removes zone files
- Resets hostname (optional)
- Cleans resolver config

---

## Configuration Options

You'll be prompted to configure:

- Network interface  
- DNS server IP  
- Subnet mask  
- Gateway  
- Domain name  
- Hostname  
- Admin email  
- Client hosts  
- DNS forwarders  

---

## Example Configuration

```plaintext
Distribution: Ubuntu 22.04
Interface: ens33
DNS IP: 192.168.86.200/24
Gateway: 192.168.86.1
Domain: example.lan
Hostname: dnsserver
Admin Email: admin@example.lan
Forwarders: 8.8.8.8, 1.1.1.1

Clients:
  dev1: 192.168.86.201
  dev2: 192.168.86.202
```

---

## Client Configuration Instructions

### Debian-based Clients

Edit Netplan config:

```bash
sudo nano /etc/netplan/01-netcfg.yaml
```

Example:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    <interface_name>:
      dhcp4: no
      addresses: [<client_ip>/24]
      routes:
        - to: default
          via: <gateway_ip>
      nameservers:
        search: [<domain_name>]
        addresses: [<dns_server_ip>, <forwarder_ip>]
```

Apply:

```bash
sudo netplan apply
```

Test DNS:

```bash
ping hostname.domain
nslookup server_ip dns_server_ip
```

### RHEL-based Clients

Using `nmcli`:

```bash
sudo nmcli connection modify <connection-name> ipv4.dns "<dns_server_ip>"
sudo nmcli connection modify <connection-name> ipv4.dns-search "<domain_name>"
sudo nmcli connection up <connection-name>
```

Or manually edit:

```bash
sudo vi /etc/sysconfig/network-scripts/ifcfg-<interface>
```

Add:

```ini
DNS1=<dns_server_ip>
DOMAIN="<domain_name>"
```

Restart:

```bash
sudo systemctl restart NetworkManager
```

Test:

```bash
ping hostname.domain
nslookup server_ip dns_server_ip
```

---

## Troubleshooting

### 1. Service Fails to Start

- Logs: `journalctl -u bind9` or `journalctl -u named`
- Syntax check: `named-checkconf`
- Zone check: `named-checkzone domain /path/to/zonefile`
- Permissions, SELinux context

### 2. Network Issues

- Debian: Check `/etc/netplan/*.yaml`, use `netplan try`
- RHEL: Check `/etc/sysconfig/network-scripts/ifcfg-*`
- Interfaces: `ip addr show`
- Ping gateway

### 3. DNS Failures

- Test local: `dig @127.0.0.1 hostname.domain`
- Forward: `dig hostname.domain @dns_server_ip`
- Reverse: `dig -x ip @dns_server_ip`
- Check firewall: `ufw status`, `firewall-cmd --list-all`

### 4. SELinux (RHEL)

- Status: `getenforce`
- Denials: `ausearch -m avc -ts recent`
- Fix: `restorecon -rv /var/named`

---

## Logs & Config Files

**Debian-based:**

- Logs: `/var/log/syslog`
- Net: `journalctl -u systemd-networkd`
- Config: `/etc/bind/named.conf.*`, zone files in `/etc/bind/`

**RHEL-based:**

- Logs: `/var/log/messages` or `journalctl -u named`
- Net: `journalctl -u NetworkManager`
- Config: `/etc/named.conf`, zone files in `/var/named/`

---

## Backup and Restore

The script automatically creates backups of:

- Network configuration files before making changes
- DNS configuration files (if reconfiguring an existing installation)


These backups can be used to restore the system if needed, either through the script's uninstall process or manually.

---

## Security Considerations

- DNS traffic (port 53 TCP/UDP) is allowed via firewall
- SELinux contexts configured (RHEL)
- Zone transfers disabled
- File permissions are secured

**Optional Security Enhancements:**

- DNSSEC  
- DoT/DoH  
- ACLs for queries  
- Routine updates  

---

## Contributing

Pull requests welcome:

1. Fork this repo  
2. Create a branch: `git checkout -b feature/amazing-feature`  
3. Commit: `git commit -m 'Add some amazing feature'`  
4. Push: `git push origin feature/amazing-feature`  
5. Open a PR  

---

## Acknowledgements

- BIND9 Documentation  
- Netplan & NetworkManager Docs  
- The Linux Community ❤️
