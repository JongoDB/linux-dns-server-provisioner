#!/usr/bin/env python3

import os
import re
import subprocess
import ipaddress
import socket
import time
import sys
import glob
import platform
from getpass import getpass

# ANSI color codes for better readability
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class LinuxDistro:
    """Class to identify and store Linux distribution information"""
    def __init__(self):
        self.is_debian_based = False
        self.is_rhel_based = False
        self.name = "Unknown"
        self.version = "Unknown"
        self.detect_distro()
    
    def detect_distro(self):
        """Detect the Linux distribution"""
        # First try lsb_release if available (most reliable)
        try:
            lsb_id = subprocess.run(["lsb_release", "-is"], check=False, stdout=subprocess.PIPE, text=True).stdout.strip().lower()
            lsb_release = subprocess.run(["lsb_release", "-rs"], check=False, stdout=subprocess.PIPE, text=True).stdout.strip()
            
            if lsb_id:
                if lsb_id in ['ubuntu', 'debian', 'linuxmint']:
                    self.is_debian_based = True
                    self.name = lsb_id.capitalize()
                elif lsb_id in ['rhel', 'centos', 'fedora', 'rocky', 'almalinux']:
                    self.is_rhel_based = True
                    self.name = lsb_id.capitalize()
                    if lsb_id == 'rhel':
                        self.name = "RHEL"
                    elif lsb_id == 'almalinux':
                        self.name = "AlmaLinux"
                
                if lsb_release:
                    self.version = lsb_release
                return
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # If lsb_release failed, try reading os-release file
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                os_info = f.read().lower()
                
                # Extract name
                name_match = re.search(r'id="?([^"\n]+)"?', os_info)
                if name_match:
                    distro_id = name_match.group(1).lower()
                    
                    # Debian-based detection
                    if distro_id in ['ubuntu', 'debian', 'linuxmint']:
                        self.is_debian_based = True
                        self.name = distro_id.capitalize()
                    
                    # RHEL-based detection
                    elif distro_id in ['rhel', 'centos', 'fedora', 'rocky', 'almalinux']:
                        self.is_rhel_based = True
                        self.name = distro_id.capitalize()
                        if distro_id == 'rhel':
                            self.name = "RHEL"
                        elif distro_id == 'almalinux':
                            self.name = "AlmaLinux"
                
                # Extract version
                version_match = re.search(r'VERSION_ID="?([^"\n]+)"?', os_info)
                if version_match:
                    self.version = version_match.group(1)
        
        # If still unknown, try distribution-specific files
        if self.name == "Unknown" or self.version == "Unknown":
            # Debian-specific
            if os.path.exists('/etc/debian_version'):
                self.is_debian_based = True
                with open('/etc/debian_version', 'r') as f:
                    debian_version = f.read().strip()
                
                if os.path.exists('/etc/lsb-release'):
                    with open('/etc/lsb-release', 'r') as f:
                        lsb_content = f.read().lower()
                        if 'ubuntu' in lsb_content:
                            self.name = "Ubuntu"
                            ubuntu_version = re.search(r'distrib_release=([^\n]+)', lsb_content)
                            if ubuntu_version:
                                self.version = ubuntu_version.group(1)
                else:
                    self.name = "Debian"
                    self.version = debian_version
            
            # RHEL-specific
            elif os.path.exists('/etc/redhat-release'):
                self.is_rhel_based = True
                with open('/etc/redhat-release', 'r') as f:
                    redhat_info = f.read().lower()
                    
                    if 'rocky' in redhat_info:
                        self.name = "Rocky Linux"
                    elif 'alma' in redhat_info:
                        self.name = "AlmaLinux"
                    elif 'centos' in redhat_info:
                        self.name = "CentOS"
                    elif 'fedora' in redhat_info:
                        self.name = "Fedora"
                    else:
                        self.name = "RHEL"
                    
                    version_match = re.search(r'release\s+(\d+(\.\d+)?)', redhat_info)
                    if version_match:
                        self.version = version_match.group(1)
                
                # Try to get more precise version using rpm if available
                try:
                    if self.name == "Rocky Linux":
                        rpm_cmd = ["rpm", "-q", "--qf", "%{VERSION}", "rocky-release"]
                    elif self.name == "AlmaLinux":
                        rpm_cmd = ["rpm", "-q", "--qf", "%{VERSION}", "almalinux-release"]
                    elif self.name == "CentOS":
                        rpm_cmd = ["rpm", "-q", "--qf", "%{VERSION}", "centos-release"]
                    elif self.name == "Fedora":
                        rpm_cmd = ["rpm", "-q", "--qf", "%{VERSION}", "fedora-release"]
                    elif self.name == "RHEL":
                        rpm_cmd = ["rpm", "-q", "--qf", "%{VERSION}", "redhat-release"]
                    
                    rpm_version = subprocess.run(rpm_cmd, check=False, stdout=subprocess.PIPE, text=True).stdout.strip()
                    if rpm_version and not rpm_version.startswith("package "):
                        self.version = rpm_version
                except (FileNotFoundError, subprocess.SubprocessError):
                    pass
        
        # If still unknown, try using platform module as fallback
        if self.name == "Unknown" or self.version == "Unknown":
            try:
                # platform.linux_distribution() is deprecated in Python 3.8+
                # Try platform.freedesktop_os_release() for newer Python versions
                try:
                    os_release = platform.freedesktop_os_release()
                    self.name = os_release.get('NAME', 'Unknown')
                    self.version = os_release.get('VERSION_ID', 'Unknown')
                except:
                    # Fallback to older method
                    try:
                        distro_info = platform.linux_distribution()
                        self.name = distro_info[0]
                        self.version = distro_info[1]
                    except:
                        pass
                
                # Determine family based on name
                if self.name.lower() in ['ubuntu', 'debian', 'linuxmint']:
                    self.is_debian_based = True
                elif self.name.lower() in ['rhel', 'centos', 'fedora', 'rocky', 'almalinux']:
                    self.is_rhel_based = True
            except:
                pass

def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")

def print_step(message):
    """Print a formatted step message"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}[+] {message}{Colors.ENDC}")

def print_success(message):
    """Print a formatted success message"""
    print(f"{Colors.GREEN}{Colors.BOLD}✓ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a formatted warning message"""
    print(f"{Colors.YELLOW}{Colors.BOLD}⚠ {message}{Colors.ENDC}")

def print_error(message):
    """Print a formatted error message"""
    print(f"{Colors.RED}{Colors.BOLD}✗ {message}{Colors.ENDC}")

def run_command(command, check=True, shell=False):
    """Run a shell command and return the result"""
    try:
        if isinstance(command, str) and not shell:
            command = command.split()
        result = subprocess.run(command, check=check, shell=shell, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        print(f"Error output: {e.stderr}")
        if check:
            return None
        return e

def check_root():
    """Check if the script is running with root privileges"""
    if os.geteuid() != 0:
        print_error("This script must be run as root (sudo).")
        sys.exit(1)

def is_valid_ip(ip):
    """Check if the provided string is a valid IP address"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_valid_domain(domain):
    """Check if the provided string is a valid domain name"""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, domain))

def is_valid_hostname(hostname):
    """Check if the provided string is a valid hostname"""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    return bool(re.match(pattern, hostname))

def get_network_interfaces():
    """Get a list of available network interfaces"""
    interfaces = []
    try:
        result = run_command("ip -o link show")
        for line in result.stdout.splitlines():
            interface = line.split()[1].split(':')[0]
            if interface != 'lo':  # Skip loopback
                interfaces.append(interface)
        return interfaces
    except Exception as e:
        print_error(f"Failed to get network interfaces: {e}")
        return []

class DNSServerManager:
    """Class to manage DNS server installation and configuration"""
    def __init__(self):
        self.distro = LinuxDistro()
        
        # Set distribution-specific variables
        if self.distro.is_debian_based:
            self.pkg_manager = "apt"
            self.pkg_install_cmd = "apt install -y"
            self.pkg_update_cmd = "apt update"
            self.pkg_remove_cmd = "apt remove -y"
            self.pkg_purge_cmd = "apt purge -y"
            self.service_name = "bind9"
            self.config_dir = "/etc/bind"
            self.zone_dir = "/etc/bind"
            self.default_hostname = "ubuntu"
        elif self.distro.is_rhel_based:
            self.pkg_manager = "dnf"
            self.pkg_install_cmd = "dnf install -y"
            self.pkg_update_cmd = "dnf check-update"
            self.pkg_remove_cmd = "dnf remove -y"
            self.pkg_purge_cmd = "dnf remove -y"  # No direct purge equivalent
            self.service_name = "named"
            self.config_dir = "/etc"
            self.zone_dir = "/var/named"
            self.default_hostname = "rocky"
        else:
            print_error(f"Unsupported Linux distribution: {self.distro.name}")
            print_warning("This script supports Debian-based (Ubuntu, Debian) and RHEL-based (Rocky, CentOS, RHEL) distributions.")
            response = input("Do you want to continue anyway? (y/n): ").lower()
            if response != 'y':
                sys.exit(1)
            
            # Ask user to specify distribution type
            print("\nPlease specify your distribution type:")
            print("1. Debian-based (Ubuntu, Debian, etc.)")
            print("2. RHEL-based (Rocky, CentOS, RHEL, etc.)")
            
            while True:
                choice = input("Enter your choice (1 or 2): ")
                if choice == '1':
                    self.distro.is_debian_based = True
                    self.distro.name = "Debian-based"
                    self.pkg_manager = "apt"
                    self.pkg_install_cmd = "apt install -y"
                    self.pkg_update_cmd = "apt update"
                    self.pkg_remove_cmd = "apt remove -y"
                    self.pkg_purge_cmd = "apt purge -y"
                    self.service_name = "bind9"
                    self.config_dir = "/etc/bind"
                    self.zone_dir = "/etc/bind"
                    self.default_hostname = "ubuntu"
                    break
                elif choice == '2':
                    self.distro.is_rhel_based = True
                    self.distro.name = "RHEL-based"
                    self.pkg_manager = "dnf"
                    self.pkg_install_cmd = "dnf install -y"
                    self.pkg_update_cmd = "dnf check-update"
                    self.pkg_remove_cmd = "dnf remove -y"
                    self.pkg_purge_cmd = "dnf remove -y"
                    self.service_name = "named"
                    self.config_dir = "/etc"
                    self.zone_dir = "/var/named"
                    self.default_hostname = "rocky"
                    break
                else:
                    print_error("Invalid choice. Please enter 1 or 2.")
    
    def is_dns_server_installed(self):
        """Check if the server is already configured as a DNS server"""
        if self.distro.is_debian_based:
            # Check if BIND9 is installed
            bind_installed = run_command(f"dpkg -l | grep {self.service_name}", check=False, shell=True).returncode == 0
            
            # Check if BIND9 service is active
            bind_active = run_command(f"systemctl is-active {self.service_name}", check=False).returncode == 0
            
            # Check if named.conf.local has zone definitions
            zones_configured = False
            if os.path.exists(f'{self.config_dir}/named.conf.local'):
                with open(f'{self.config_dir}/named.conf.local', 'r') as f:
                    content = f.read()
                    zones_configured = 'zone' in content
            
            return bind_installed and (bind_active or zones_configured)
        
        elif self.distro.is_rhel_based:
            # Check if BIND is installed
            bind_installed = run_command(f"rpm -q bind", check=False).returncode == 0
            
            # Check if BIND service is active
            bind_active = run_command(f"systemctl is-active {self.service_name}", check=False).returncode == 0
            
            # Check if named.conf has zone definitions
            zones_configured = False
            if os.path.exists('/etc/named/named.conf.local'):
                with open('/etc/named/named.conf.local', 'r') as f:
                    content = f.read()
                    zones_configured = 'zone' in content
            elif os.path.exists('/etc/named.conf'):
                with open('/etc/named.conf', 'r') as f:
                    content = f.read()
                    zones_configured = 'zone' in content and ('type master' in content or 'type slave' in content)
            
            return bind_installed and (bind_active or zones_configured)
        
        return False
    
    def get_user_input(self):
        """Gather all necessary information from the user"""
        print_header("DNS Server Configuration")
        
        # Get network interface
        interfaces = get_network_interfaces()
        if not interfaces:
            print_error("No network interfaces found.")
            sys.exit(1)
        
        print("Available network interfaces:")
        for i, interface in enumerate(interfaces, 1):
            print(f"{i}. {interface}")
        
        while True:
            try:
                choice = int(input("\nSelect network interface (number): "))
                if 1 <= choice <= len(interfaces):
                    interface = interfaces[choice-1]
                    break
                else:
                    print_error("Invalid selection. Please try again.")
            except ValueError:
                print_error("Please enter a number.")
        
        # Get DNS server IP
        while True:
            server_ip = input("\nEnter DNS server IP address [192.168.86.200]: ").strip() or "192.168.86.200"
            if is_valid_ip(server_ip):
                break
            else:
                print_error("Invalid IP address. Please try again.")
        
        # Get subnet information
        while True:
            subnet_mask = input("\nEnter subnet mask [24]: ").strip() or "24"
            try:
                subnet_mask = int(subnet_mask)
                if 0 <= subnet_mask <= 32:
                    break
                else:
                    print_error("Subnet mask must be between 0 and 32.")
            except ValueError:
                print_error("Please enter a valid number.")
        
        # Get gateway IP
        while True:
            gateway_ip = input("\nEnter gateway IP address [192.168.86.1]: ").strip() or "192.168.86.1"
            if is_valid_ip(gateway_ip):
                break
            else:
                print_error("Invalid IP address. Please try again.")
        
        # Get domain name
        default_domain = "jondev.lan" if self.distro.is_debian_based else "rockydns.lan"
        while True:
            domain_name = input(f"\nEnter domain name [{default_domain}]: ").strip() or default_domain
            if is_valid_domain(domain_name):
                break
            else:
                print_error("Invalid domain name. Please try again.")
        
        # Get hostname
        default_hostname = "ubudns" if self.distro.is_debian_based else "rockydns"
        while True:
            hostname = input(f"\nEnter DNS server hostname [{default_hostname}]: ").strip() or default_hostname
            if is_valid_hostname(hostname):
                break
            else:
                print_error("Invalid hostname. Please try again.")
        
        # Get admin email
        while True:
            admin_email = input("\nEnter admin email [admin@" + domain_name + "]: ").strip() or f"admin@{domain_name}"
            if '@' in admin_email:
                break
            else:
                print_error("Invalid email address. Please try again.")
        
        # Get client information
        clients = []
        print("\nNow let's configure client hosts (dev1, dev2, etc.)")
        print(f"{Colors.BOLD}Enter 'done', 'exit', or 'q' when finished adding clients.{Colors.ENDC}")
        
        ip_base = server_ip.rsplit('.', 1)[0]
        next_ip = int(server_ip.split('.')[-1]) + 1
        
        while True:
            default_hostname = f"dev{len(clients)+1}"
            default_ip = f"{ip_base}.{next_ip}"
            
            client_hostname = input(f"\nEnter client hostname [{default_hostname}] (or 'done' to finish): ").strip() or default_hostname
            
            # Check for exit commands
            if client_hostname.lower() in ['done', 'exit', 'q', 'quit', 'finish']:
                break
                
            if not is_valid_hostname(client_hostname):
                print_error("Invalid hostname. Please try again.")
                continue
            
            client_ip = input(f"Enter IP for {client_hostname} [{default_ip}]: ").strip() or default_ip
            if not is_valid_ip(client_ip):
                print_error("Invalid IP address. Please try again.")
                continue
            
            clients.append((client_hostname, client_ip))
            next_ip += 1
            
            if len(clients) >= 10:  # Limit to 10 clients for simplicity
                print_warning("Maximum number of clients reached.")
                break
            
            print(f"Added {client_hostname} with IP {client_ip}")
            print(f"Current client count: {len(clients)}")
            print(f"{Colors.BOLD}Enter 'done' to finish adding clients or continue with the next client.{Colors.ENDC}")
        
        # Get DNS forwarders
        forwarders = ["8.8.8.8", "1.1.1.1"]  # Default forwarders
        custom_forwarders = input("\nEnter custom DNS forwarders (comma-separated) or press Enter for defaults [8.8.8.8,1.1.1.1]: ").strip()
        if custom_forwarders:
            forwarders = [f.strip() for f in custom_forwarders.split(',')]
            # Validate each forwarder
            for forwarder in forwarders:
                if not is_valid_ip(forwarder):
                    print_warning(f"Invalid forwarder IP: {forwarder}. Using defaults instead.")
                    forwarders = ["8.8.8.8", "1.1.1.1"]
                    break
        
        # Confirm settings
        print_header("Configuration Summary")
        print(f"Distribution: {self.distro.name} {self.distro.version}")
        print(f"Network Interface: {interface}")
        print(f"DNS Server IP: {server_ip}/{subnet_mask}")
        print(f"Gateway IP: {gateway_ip}")
        print(f"Domain Name: {domain_name}")
        print(f"Hostname: {hostname}")
        print(f"Admin Email: {admin_email}")
        print(f"DNS Forwarders: {', '.join(forwarders)}")
        print("\nClient Hosts:")
        for client_hostname, client_ip in clients:
            print(f"  {client_hostname}: {client_ip}")
        
        confirm = input("\nProceed with this configuration? (y/n): ").lower()
        if confirm != 'y':
            print("Setup cancelled.")
            sys.exit(0)
        
        # Calculate network information for reverse DNS
        network = ipaddress.IPv4Network(f"{server_ip}/{subnet_mask}", strict=False)
        reverse_zone = '.'.join(reversed(str(network.network_address).split('.')[:3])) + '.in-addr.arpa'
        
        return {
            'interface': interface,
            'server_ip': server_ip,
            'subnet_mask': subnet_mask,
            'gateway_ip': gateway_ip,
            'domain_name': domain_name,
            'hostname': hostname,
            'admin_email': admin_email.replace('@', '.'),  # Format for SOA record
            'clients': clients,
            'forwarders': forwarders,
            'reverse_zone': reverse_zone,
            'network': network
        }
    
    def set_hostname(self, hostname):
        """Set the system hostname"""
        print_step("Setting system hostname...")
        
        # Get current hostname for backup
        current_hostname = run_command("hostname", check=False).stdout.strip()
        
        # Only change if different
        if current_hostname != hostname:
            run_command(f"hostnamectl set-hostname {hostname}")
            
            # Update /etc/hosts
            with open('/etc/hosts', 'r') as f:
                hosts_content = f.read()
            
            # Check if hostname already exists in /etc/hosts
            if not re.search(rf'\s{hostname}(\s|$)', hosts_content):
                with open('/etc/hosts', 'a') as f:
                    f.write(f"\n127.0.1.1\t{hostname}\n")
            
            print_success(f"Hostname set to {hostname}")
        else:
            print_success(f"Hostname already set to {hostname}")
    
    def configure_network(self, config):
        """Configure network settings based on the distribution"""
        if self.distro.is_debian_based:
            self.configure_netplan(config)
        elif self.distro.is_rhel_based:
            self.configure_networkmanager(config)
        else:
            print_error("Unsupported distribution for network configuration")
            sys.exit(1)
    
    def configure_netplan(self, config):
        """Configure network settings using Netplan (Debian-based)"""
        print_step("Configuring network settings using Netplan...")
        
        # Backup existing netplan files
        netplan_dir = '/etc/netplan'
        netplan_files = [f for f in os.listdir(netplan_dir) if f.endswith('.yaml')]
        
        for file in netplan_files:
            backup_file = f"{netplan_dir}/{file}.bak"
            if not os.path.exists(backup_file):
                run_command(f"cp {netplan_dir}/{file} {backup_file}")
    
    # Create a new netplan configuration file
        netplan_config = f"""network:
  version: 2
  renderer: networkd
  ethernets:
    {config['interface']}:
      dhcp4: no
      addresses: [{config['server_ip']}/{config['subnet_mask']}]
      routes:
        - to: default
          via: {config['gateway_ip']}
      nameservers:
        search: [{config['domain_name']}]
        addresses: [{', '.join(config['forwarders'])}]
"""
    
    # Write new config to a temporary file first
        temp_file = '/tmp/netplan_config.yaml'
        with open(temp_file, 'w') as f:
            f.write(netplan_config)
    
    # Validate the config
        result = run_command(f"netplan try --timeout 30 --config {temp_file}", check=False)
        if result.returncode != 0:
            print_error("Invalid netplan configuration.")
            print("Error details:")
            print(result.stderr)
            return False
    
    # Remove any existing DNS server config files to avoid conflicts
        for file in os.listdir(netplan_dir):
            if file.startswith('01-dns-server') or file.startswith('50-cloud-init') or file.startswith('00-installer-config'):
                os.remove(f"{netplan_dir}/{file}")
    
    # Copy to actual location
        with open(f"{netplan_dir}/01-dns-server.yaml", 'w') as f:
            f.write(netplan_config)
    
    # Apply netplan config
        result = run_command("netplan apply", check=False)
        if result.returncode != 0:
            print_error("Failed to apply network configuration.")
            print("Error details:")
            print(result.stderr)
        
        # Offer to restore backup
            restore = input("Would you like to restore the backup configuration? (y/n): ").lower()
            if restore == 'y':
            # Remove the new file
                if os.path.exists(f"{netplan_dir}/01-dns-server.yaml"):
                    os.remove(f"{netplan_dir}/01-dns-server.yaml")
                run_command("netplan apply")
                print_warning("Restored previous network configuration.")
                sys.exit(1)
        else:
            print_success("Network configuration applied successfully")
    
    def configure_networkmanager(self, config):
        """Configure network settings using NetworkManager (RHEL-based)"""
        print_step("Configuring network settings using NetworkManager...")
    
    # Check if NetworkManager is installed and running
        nm_running = run_command("systemctl is-active NetworkManager", check=False).returncode == 0
    
        if not nm_running:
            print_warning("NetworkManager is not running. Installing and enabling it...")
            run_command(f"{self.pkg_install_cmd} NetworkManager")
            run_command("systemctl enable --now NetworkManager")
    
    # Get current connection name for the interface
        conn_name = None
        result = run_command(f"nmcli -t -f NAME,DEVICE connection show", check=False)
        for line in result.stdout.splitlines():
            if ':' in line and config['interface'] in line.split(':')[1]:
                conn_name = line.split(':')[0]
                break
    
        if not conn_name:
        # Create a new connection if none exists
            print_warning(f"No connection found for interface {config['interface']}. Creating a new one...")
            conn_name = f"{config['interface']}-static"
            run_command(f"nmcli connection add type ethernet con-name {conn_name} ifname {config['interface']}")
    
    # Backup the connection
        backup_dir = "/tmp/network-backups"
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = f"{backup_dir}/{conn_name.replace(' ', '_')}-{int(time.time())}.nmconnection"
        run_command(f"nmcli connection export '{conn_name}' > {backup_file}", check=False, shell=True)
        print_success(f"Connection backup saved to {backup_file}")
    
    # Configure the connection with static IP
        print_step(f"Configuring static IP for {conn_name}...")
    
        try:
        # Delete any existing IP addresses first
            run_command(f"nmcli connection modify '{conn_name}' ipv4.addresses ''", shell=True)
        
        # Set IP address first, then method to manual (order matters)
            run_command(f"nmcli connection modify '{conn_name}' ipv4.addresses {config['server_ip']}/{config['subnet_mask']}", shell=True)
            run_command(f"nmcli connection modify '{conn_name}' ipv4.method manual", shell=True)
        
        # Set gateway
            run_command(f"nmcli connection modify '{conn_name}' ipv4.gateway {config['gateway_ip']}", shell=True)
        
        # Set DNS servers as a space-separated list
            dns_servers = " ".join(config['forwarders'])
            run_command(f"nmcli connection modify '{conn_name}' ipv4.dns '{dns_servers}'", shell=True)
        
        # Set DNS search domain
            run_command(f"nmcli connection modify '{conn_name}' ipv4.dns-search {config['domain_name']}", shell=True)
        
        # Apply the changes
            run_command(f"nmcli connection up '{conn_name}'", shell=True)
        
        # Verify the connection
            result = run_command(f"nmcli connection show '{conn_name}'", check=False, shell=True)
            if "ipv4.method:                            manual" not in result.stdout:
                print_error("Failed to configure static IP. Connection may not be working properly.")
                print("Connection details:")
                print(result.stdout)
            
            # Offer to restore backup
                restore = input("Would you like to restore the backup configuration? (y/n): ").lower()
                if restore == 'y':
                    self.restore_networkmanager_backup(conn_name, backup_file, config['interface'])
                    sys.exit(1)
            else:
                print_success("Network configuration applied successfully")
            
        except Exception as e:
            print_error(f"Failed to configure network: {e}")
        
        # Offer to restore backup
            restore = input("Would you like to restore the backup configuration? (y/n): ").lower()
            if restore == 'y':
                self.restore_networkmanager_backup(conn_name, backup_file, config['interface'])
                sys.exit(1)
    
    def restore_networkmanager_backup(self, conn_name, backup_file, interface):
        """Restore NetworkManager connection from backup"""
        print_warning("Restoring backup configuration. This may temporarily disconnect your network...")
        
        # Create a temporary connection to maintain connectivity
        temp_conn_name = f"{conn_name}-temp"
        run_command(f"nmcli connection clone '{conn_name}' '{temp_conn_name}'", check=False, shell=True)
        run_command(f"nmcli connection up '{temp_conn_name}'", check=False, shell=True)
        
        # Delete the problematic connection
        run_command(f"nmcli connection delete '{conn_name}'", check=False, shell=True)
        
        # Import the backup with a new name to avoid conflicts
        new_conn_name = f"{conn_name}-restored"
        run_command(f"nmcli connection import type nmcli file '{backup_file}' name '{new_conn_name}'", check=False, shell=True)
        
        # Activate the restored connection
        run_command(f"nmcli connection modify '{new_conn_name}' connection.interface-name {interface}", shell=True)
        run_command(f"nmcli connection up '{new_conn_name}'", check=False, shell=True)
        
        # Delete the temporary connection
        run_command(f"nmcli connection delete '{temp_conn_name}'", check=False, shell=True)
        
        print_warning("Restored previous network configuration. If you're still connected, the restore was successful.")
        print_warning(f"Your connection is now named '{new_conn_name}'")
    
    def install_dns_server(self):
        """Install DNS server"""
        # Get user input
        config = self.get_user_input()
    
    # Set hostname
        self.set_hostname(config['hostname'])
    
    # Configure network
        self.configure_network(config)
    
    # Install DNS server packages
        if self.distro.is_debian_based:
            self.install_bind9()
        elif self.distro.is_rhel_based:
            self.install_bind()
        else:
            print_error("Unsupported distribution for DNS server installation")
            sys.exit(1)
    
    # Configure DNS server
        self.configure_dns_server(config)
    
    # Configure firewall
        self.configure_firewall()
    
    # Restart DNS server
        self.restart_dns_server()
    
    # Verify DNS server
        self.verify_dns_server(config)
    
    # Print client configuration instructions
        self.print_client_instructions(config)
    
        print_header("DNS Server Setup Complete")
        print(f"""
Your DNS server has been successfully set up with the following configuration:

Server Hostname: {config['hostname']}.{config['domain_name']}
Server IP: {config['server_ip']}
Domain: {config['domain_name']}

You can now configure your client devices to use this DNS server.
""")
    
    def install_bind9(self):
        """Install BIND9 DNS server (Debian-based)"""
        print_step("Installing BIND9 DNS server...")
        
        # Update package lists
        run_command(f"{self.pkg_update_cmd}")
        
        # Install BIND9 packages
        run_command(f"{self.pkg_install_cmd} bind9 bind9utils bind9-doc")
        
        # Check if BIND9 is installed and running
        result = run_command(f"systemctl is-active {self.service_name}", check=False)
        if result.returncode != 0:
            print_error("BIND9 installation failed or service is not running.")
            sys.exit(1)
        
        print_success("BIND9 installed successfully")
    
    def install_bind(self):
        """Install BIND DNS server (RHEL-based)"""
        print_step("Installing BIND DNS server...")
        
        # Update package lists
        run_command(f"{self.pkg_update_cmd}", check=False)
        
        # Install BIND packages
        run_command(f"{self.pkg_install_cmd} bind bind-utils")
        
        # Enable and start the service
        run_command(f"systemctl enable {self.service_name}")
        run_command(f"systemctl start {self.service_name}")
        
        # Check if BIND is installed and running
        result = run_command(f"systemctl is-active {self.service_name}", check=False)
        if result.returncode != 0:
            print_error("BIND installation failed or service is not running.")
            sys.exit(1)
        
        print_success("BIND installed successfully")
    
    def configure_dns_server(self, config):
        """Configure DNS server based on the distribution"""
        if self.distro.is_debian_based:
            self.configure_bind9(config)
        elif self.distro.is_rhel_based:
            self.configure_bind(config)
        else:
            print_error("Unsupported distribution for DNS server configuration")
            sys.exit(1)
    
    def configure_bind9(self, config):
        """Configure BIND9 DNS server (Debian-based)"""
        print_step("Configuring BIND9...")
        
        # Configure named.conf.options
        options_content = f"""options {{
    directory "/var/cache/bind";
    
    forwarders {{
        {'; '.join(f'{forwarder}' for forwarder in config['forwarders'])};
    }};
    
    allow-query {{ any; }};
    recursion yes;
    
    dnssec-validation auto;
    listen-on {{ any; }};
}};
"""
        
        with open(f'{self.config_dir}/named.conf.options', 'w') as f:
            f.write(options_content)
        
        # Configure named.conf.local
        local_content = f"""zone "{config['domain_name']}" {{
    type master;
    file "/etc/bind/db.{config['domain_name']}";
}};

zone "{config['reverse_zone']}" {{
    type master;
    file "/etc/bind/db.{config['network'].network_address.packed[0]}";
}};
"""
        
        with open(f'{self.config_dir}/named.conf.local', 'w') as f:
            f.write(local_content)
        
        # Create forward zone file
        forward_zone = f"""$TTL    604800
@       IN      SOA     {config['hostname']}.{config['domain_name']}. {config['admin_email']}. (
                             1         ; Serial
                        604800         ; Refresh
                         86400         ; Retry
                       2419200         ; Expire
                        604800 )       ; Negative Cache TTL
;
@       IN      NS      {config['hostname']}.{config['domain_name']}.
{config['hostname']}    IN      A       {config['server_ip']}
"""
        
        # Add client records
        for client_hostname, client_ip in config['clients']:
            forward_zone += f"{client_hostname}    IN      A       {client_ip}\n"
        
        with open(f"{self.zone_dir}/db.{config['domain_name']}", 'w') as f:
            f.write(forward_zone)
        
        # Create reverse zone file
        reverse_zone = f"""$TTL    604800
@       IN      SOA     {config['hostname']}.{config['domain_name']}. {config['admin_email']}. (
                             1         ; Serial
                        604800         ; Refresh
                         86400         ; Retry
                       2419200         ; Expire
                        604800 )       ; Negative Cache TTL
;
@       IN      NS      {config['hostname']}.{config['domain_name']}.
"""
        
        # Add server PTR record
        server_ip_last_octet = config['server_ip'].split('.')[-1]
        reverse_zone += f"{server_ip_last_octet}    IN      PTR     {config['hostname']}.{config['domain_name']}.\n"
        
        # Add client PTR records
        for client_hostname, client_ip in config['clients']:
            client_ip_last_octet = client_ip.split('.')[-1]
            reverse_zone += f"{client_ip_last_octet}    IN      PTR     {client_hostname}.{config['domain_name']}.\n"
        
        with open(f"{self.zone_dir}/db.{config['network'].network_address.packed[0]}", 'w') as f:
            f.write(reverse_zone)
        
        print_success("BIND9 configuration completed")
    
    def configure_bind(self, config):
        """Configure BIND DNS server (RHEL-based)"""
        print_step("Configuring BIND...")
        
        # Create named directory if it doesn't exist
        os.makedirs('/etc/named', exist_ok=True)
        os.makedirs('/var/named', exist_ok=True)
        
        # Check if SELinux is enabled
        selinux_enabled = run_command("getenforce", check=False).stdout.strip() != "Disabled"
        
        if selinux_enabled:
            print_step("Configuring SELinux for BIND...")
            # Allow BIND to write to its directories
            run_command("setsebool -P named_write_master_zones 1")
            # Allow BIND to connect to DNS
            run_command("setsebool -P named_tcp_bind_http_port 1")
        
        # Configure named.conf
        named_conf = f"""// Named configuration for DNS Server
options {{
    listen-on port 53 {{ any; }};
    listen-on-v6 port 53 {{ ::1; }};
    directory "/var/named";
    dump-file "/var/named/data/cache_dump.db";
    statistics-file "/var/named/data/named_stats.txt";
    memstatistics-file "/var/named/data/named_mem_stats.txt";
    secroots-file "/var/named/data/named.secroots";
    recursing-file "/var/named/data/named.recursing";
    
    allow-query {{ any; }};
    allow-transfer {{ none; }};
    
    recursion yes;
    
    forwarders {{
        {'; '.join(f'{forwarder}' for forwarder in config['forwarders'])};
    }};
    
    dnssec-validation yes;
    managed-keys-directory "/var/named/dynamic";
    pid-file "/run/named/named.pid";
    session-keyfile "/run/named/session.key";
    
    /* https://fedoraproject.org/wiki/Changes/CryptoPolicy */
    include "/etc/crypto-policies/back-ends/bind.config";
}};

logging {{
    channel default_debug {{
        file "data/named.run";
        severity dynamic;
    }};
}};

zone "." IN {{
    type hint;
    file "named.ca";
}};

include "/etc/named.rfc1912.zones";
include "/etc/named.root.key";

// Forward zone for {config['domain_name']}
zone "{config['domain_name']}" IN {{
    type master;
    file "/var/named/{config['domain_name']}.zone";
    allow-update {{ none; }};
}};

// Reverse zone for {config['reverse_zone']}
zone "{config['reverse_zone']}" IN {{
    type master;
    file "/var/named/{config['reverse_zone']}.zone";
    allow-update {{ none; }};
}};
"""
        
        with open('/etc/named.conf', 'w') as f:
            f.write(named_conf)
        
        # Create forward zone file
        forward_zone = f"""$TTL    86400
@       IN      SOA     {config['hostname']}.{config['domain_name']}. {config['admin_email']}. (
                             1         ; Serial
                        604800         ; Refresh
                         86400         ; Retry
                       2419200         ; Expire
                        604800 )       ; Negative Cache TTL
;
@       IN      NS      {config['hostname']}.{config['domain_name']}.
{config['hostname']}    IN      A       {config['server_ip']}
"""
        
        # Add client records
        for client_hostname, client_ip in config['clients']:
            forward_zone += f"{client_hostname}    IN      A       {client_ip}\n"
        
        forward_zone_file = f"/var/named/{config['domain_name']}.zone"
        with open(forward_zone_file, 'w') as f:
            f.write(forward_zone)
        
        # Create reverse zone file
        reverse_zone = f"""$TTL    86400
@       IN      SOA     {config['hostname']}.{config['domain_name']}. {config['admin_email']}. (
                             1         ; Serial
                        604800         ; Refresh
                         86400         ; Retry
                       2419200         ; Expire
                        604800 )       ; Negative Cache TTL
;
@       IN      NS      {config['hostname']}.{config['domain_name']}.
"""
        
        # Add server PTR record
        server_ip_last_octet = config['server_ip'].split('.')[-1]
        reverse_zone += f"{server_ip_last_octet}    IN      PTR     {config['hostname']}.{config['domain_name']}.\n"
        
        # Add client PTR records
        for client_hostname, client_ip in config['clients']:
            client_ip_last_octet = client_ip.split('.')[-1]
            reverse_zone += f"{client_ip_last_octet}    IN      PTR     {client_hostname}.{config['domain_name']}.\n"
        
        reverse_zone_file = f"/var/named/{config['reverse_zone']}.zone"
        with open(reverse_zone_file, 'w') as f:
            f.write(reverse_zone)
        
        # Set proper permissions on specific zone files
        run_command(f"chown named:named {forward_zone_file}")
        run_command(f"chmod 640 {forward_zone_file}")
        run_command(f"chown named:named {reverse_zone_file}")
        run_command(f"chmod 640 {reverse_zone_file}")
        
        if selinux_enabled:
            # Set proper SELinux context
            run_command("restorecon -rv /var/named")
            run_command("restorecon -v /etc/named.conf")
        
        print_success("BIND configuration completed")
    
    def configure_firewall(self):
        """Configure firewall to allow DNS traffic"""
        print_step("Configuring firewall...")
        
        if self.distro.is_debian_based:
            # Check if ufw is installed and active
            ufw_active = run_command("ufw status", check=False).returncode == 0 and "Status: active" in run_command("ufw status", check=False).stdout
            
            if ufw_active:
                run_command("ufw allow 53/tcp")
                run_command("ufw allow 53/udp")
                print_success("UFW firewall configured to allow DNS traffic")
            else:
                print_warning("UFW firewall is not active. No firewall rules were added.")
        
        elif self.distro.is_rhel_based:
            # Check if firewalld is installed and running
            firewalld_running = run_command("systemctl is-active firewalld", check=False).returncode == 0
            
            if not firewalld_running:
                print_warning("Firewalld is not running. Installing and enabling it...")
                run_command(f"{self.pkg_install_cmd} firewalld")
                run_command("systemctl enable --now firewalld")
            
            # Allow DNS service
            run_command("firewall-cmd --add-service=dns --permanent")
            
            # Reload firewall
            run_command("firewall-cmd --reload")
            
            print_success("Firewall configured to allow DNS traffic")
    
    def restart_dns_server(self):
        """Restart DNS server based on the distribution"""
        print_step(f"Restarting {self.service_name} service...")
        
        run_command(f"systemctl restart {self.service_name}")
        
        # Check if service is running
        result = run_command(f"systemctl is-active {self.service_name}", check=False)
        if result.returncode != 0:
            print_error(f"Failed to restart {self.service_name} service.")
            
            # Check for errors in the logs
            log_result = run_command(f"journalctl -u {self.service_name} --no-pager -n 20", check=False)
            print(f"{self.service_name} service logs:")
            print(log_result.stdout)
            
            fix = input("Would you like to try to fix common configuration errors? (y/n): ").lower()
            if fix == 'y':
                # Check zone files syntax
                if self.distro.is_debian_based:
                    run_command("named-checkconf", check=False)
                elif self.distro.is_rhel_based:
                    run_command("named-checkconf /etc/named.conf", check=False)
                sys.exit(1)
        
        print_success(f"{self.service_name} service restarted successfully")
    
    def verify_dns_server(self, config):
        """Verify DNS server is working correctly"""
        print_step("Verifying DNS server functionality...")
        
        # Wait a moment for BIND to fully start
        time.sleep(2)
        
        # Test forward lookup for the server itself
        server_fqdn = f"{config['hostname']}.{config['domain_name']}"
        print(f"Testing forward lookup for {server_fqdn}...")
        
        dig_result = run_command(f"dig {server_fqdn} @127.0.0.1", check=False)
        if "ANSWER SECTION" not in dig_result.stdout or config['server_ip'] not in dig_result.stdout:
            print_error(f"Forward lookup test failed for {server_fqdn}")
            print(dig_result.stdout)
        else:
            print_success(f"Forward lookup test passed for {server_fqdn}")
        
        # Test reverse lookup for the server
        print(f"Testing reverse lookup for {config['server_ip']}...")
        
        dig_result = run_command(f"dig -x {config['server_ip']} @127.0.0.1", check=False)
        if "ANSWER SECTION" not in dig_result.stdout or server_fqdn not in dig_result.stdout:
            print_error(f"Reverse lookup test failed for {config['server_ip']}")
            print(dig_result.stdout)
        else:
            print_success(f"Reverse lookup test passed for {config['server_ip']}")
        
        # Test forward lookup for a client
        if config['clients']:
            client_hostname, client_ip = config['clients'][0]
            client_fqdn = f"{client_hostname}.{config['domain_name']}"
            
            print(f"Testing forward lookup for {client_fqdn}...")
            
            dig_result = run_command(f"dig {client_fqdn} @127.0.0.1", check=False)
            if "ANSWER SECTION" not in dig_result.stdout or client_ip not in dig_result.stdout:
                print_error(f"Forward lookup test failed for {client_fqdn}")
                print(dig_result.stdout)
            else:
                print_success(f"Forward lookup test passed for {client_fqdn}")
            
            # Test reverse lookup for a client
            print(f"Testing reverse lookup for {client_ip}...")
            
            dig_result = run_command(f"dig -x {client_ip} @127.0.0.1", check=False)
            if "ANSWER SECTION" not in dig_result.stdout or client_fqdn not in dig_result.stdout:
                print_error(f"Reverse lookup test failed for {client_ip}")
                print(dig_result.stdout)
            else:
                print_success(f"Reverse lookup test passed for {client_ip}")
    
    def print_client_instructions(self, config):
        """Print instructions for configuring client devices"""
        print_header("Client Configuration Instructions")
        
        if self.distro.is_debian_based:
            print(f"""
To configure DNS on Linux clients using Netplan:

1. Edit Netplan config:
   sudo nano /etc/netplan/01-netcfg.yaml

   Example for static IP:
   network:
     version: 2
     renderer: networkd
     ethernets:
       <interface_name>:
         dhcp4: no
         addresses: [<client_ip>/24]
         routes:
           - to: default
             via: {config['gateway_ip']}
         nameservers:
           search: [{config['domain_name']}]
           addresses: [{config['server_ip']}, {config['forwarders'][0]}]

   Apply changes:
   sudo netplan apply

2. Test DNS:
   ping {config['hostname']}.{config['domain_name']}
   nslookup {config['server_ip']} {config['server_ip']}
""")
        elif self.distro.is_rhel_based:
            print(f"""
To configure DNS on Rocky Linux/RHEL clients:

1. Using NetworkManager CLI:
   sudo nmcli connection modify <connection-name> ipv4.dns "{config['server_ip']}"
   sudo nmcli connection modify <connection-name> ipv4.dns-search "{config['domain_name']}"
   sudo nmcli connection up <connection-name>

2. Or edit the network script directly:
   sudo vi /etc/sysconfig/network-scripts/ifcfg-<interface>
   
   Add or modify these lines:
   DNS1={config['server_ip']}
   DOMAIN="{config['domain_name']}"
   
   Then restart the network:
   sudo systemctl restart NetworkManager

3. Test DNS:
   ping {config['hostname']}.{config['domain_name']}
   nslookup {config['server_ip']} {config['server_ip']}
""")
    
    def confirm_uninstall(self):
        """Confirm with the user before proceeding with uninstallation"""
        print_header("DNS Server Uninstallation")
        print(f"{Colors.YELLOW}{Colors.BOLD}WARNING: This will remove the DNS server configuration.{Colors.ENDC}")
        print(f"{Colors.YELLOW}The following actions will be performed:{Colors.ENDC}")
        print(f"  1. Stop and disable the {self.service_name} service")
        print("  2. Remove BIND packages")
        print("  3. Restore original network configuration")
        print("  4. Remove DNS zone files")
        print("  5. Reset hostname (optional)")
        print("\nThis process cannot be undone. Make sure you have backups if needed.")
        
        confirm = input(f"\n{Colors.BOLD}Are you sure you want to proceed? (yes/no): {Colors.ENDC}").lower()
        if confirm != 'yes':
            print("Uninstallation cancelled.")
            sys.exit(0)
    
    def stop_dns_service(self):
        """Stop and disable the DNS service"""
        print_step(f"Stopping and disabling {self.service_name} service...")
        
        # Check if service is installed
        result = run_command(f"systemctl status {self.service_name}", check=False)
        if result.returncode != 0:
            print_warning(f"{self.service_name} service not found. Skipping this step.")
            return
        
        # Stop and disable the service
        run_command(f"systemctl stop {self.service_name}", check=False)
        run_command(f"systemctl disable {self.service_name}", check=False)
        
        print_success(f"{self.service_name} service stopped and disabled")
    
    def remove_dns_packages(self):
        """Remove DNS packages based on the distribution"""
        print_step("Removing DNS packages...")
        
        if self.distro.is_debian_based:
            # Check if BIND9 is installed
            result = run_command("dpkg -l | grep bind9", check=False, shell=True)
            if result.returncode != 0 or not result.stdout.strip():
                print_warning("BIND9 packages not found. Skipping this step.")
                return
            
            # Ask user if they want to remove configuration files as well
            purge = input("Do you want to remove configuration files as well? (y/n): ").lower() == 'y'
            
            # Remove packages
            if purge:
                run_command("apt purge -y bind9 bind9utils bind9-doc", check=False)
            else:
                run_command("apt remove -y bind9 bind9utils bind9-doc", check=False)
        
        elif self.distro.is_rhel_based:
            # Check if BIND is installed
            result = run_command("rpm -q bind", check=False)
            if result.returncode != 0:
                print_warning("BIND packages not found. Skipping this step.")
                return
            
            # Ask user if they want to remove configuration files as well
            purge = input("Do you want to remove configuration files as well? (y/n): ").lower() == 'y'
            
            # Remove packages
            if purge:
                run_command("dnf remove -y bind bind-utils", check=False)
                run_command("rm -rf /var/named/*.zone /etc/named.conf", check=False)
            else:
                run_command("dnf remove -y bind bind-utils", check=False)
        
        print_success("DNS packages removed")
    
    def restore_network_configuration(self):
        """Restore original network configuration based on the distribution"""
        if self.distro.is_debian_based:
            self.restore_netplan_configuration()
        elif self.distro.is_rhel_based:
            self.restore_networkmanager_configuration()
        else:
            print_error("Unsupported distribution for network configuration restoration")
    
    def restore_netplan_configuration(self):
        """Restore original Netplan configuration (Debian-based)"""
        print_step("Restoring network configuration...")
        
        netplan_dir = '/etc/netplan'
        
        # Remove our custom netplan file if it exists
        custom_file = f"{netplan_dir}/01-dns-server.yaml"
        if os.path.exists(custom_file):
            os.remove(custom_file)
            print_success(f"Removed custom netplan file: {custom_file}")
        
        # Restore backup files
        backup_files = glob.glob(f"{netplan_dir}/*.bak")
        
        if backup_files:
            for backup_file in backup_files:
                original_file = backup_file[:-4]  # Remove .bak extension
                run_command(f"cp {backup_file} {original_file}", check=False)
                print(f"Restored {os.path.basename(original_file)} from backup")
            
            # Apply netplan config
            result = run_command("netplan apply", check=False)
            if result.returncode != 0:
                print_error("Failed to apply network configuration.")
                print("Error details:")
                print(result.stderr)
                
                # Offer to configure DHCP
                dhcp = input("Would you like to configure DHCP instead? (y/n): ").lower() == 'y'
                if dhcp:
                    self.create_dhcp_netplan_config()
            else:
                print_success("Original network configuration restored")
            
            # Clean up backup files
            if input("Do you want to remove backup network configuration files? (y/n): ").lower() == 'y':
                for backup_file in backup_files:
                    os.remove(backup_file)
                print_success("Backup network configuration files removed")
        else:
            print_warning("No backup network configuration found.")
            
            # Ask if user wants to configure DHCP
            dhcp = input("Do you want to configure the network interface to use DHCP? (y/n): ").lower() == 'y'
            if dhcp:
                self.create_dhcp_netplan_config()
    
    def create_dhcp_netplan_config(self):
        """Create a DHCP configuration for a network interface using Netplan"""
        # Get network interfaces
        interfaces = get_network_interfaces()
        if not interfaces:
            print_error("No network interfaces found.")
            return
        
        # Select interface
        print("Available network interfaces:")
        for i, interface in enumerate(interfaces, 1):
            print(f"{i}. {interface}")
        
        while True:
            try:
                choice = int(input("\nSelect network interface to configure (number): "))
                if 1 <= choice <= len(interfaces):
                    interface = interfaces[choice-1]
                    break
                else:
                    print_error("Invalid selection. Please try again.")
            except ValueError:
                print_error("Please enter a number.")
        
        # Create DHCP configuration - use a new file to avoid modifying existing ones
        dhcp_config = f"""network:
  version: 2
  renderer: networkd
  ethernets:
    {interface}:
      dhcp4: true
"""
        
        netplan_dir = '/etc/netplan'
        with open(f"{netplan_dir}/01-dhcp.yaml", 'w') as f:
            f.write(dhcp_config)
        
        # Apply netplan config
        run_command("netplan apply", check=False)
        print_success(f"Network interface {interface} configured to use DHCP")
    
    def restore_networkmanager_configuration(self):
        """Restore original NetworkManager configuration (RHEL-based)"""
        print_step("Restoring network configuration...")
        
        # Get network interfaces
        interfaces = get_network_interfaces()
        if not interfaces:
            print_error("No network interfaces found.")
            return
        
        # Select interface
        print("Available network interfaces:")
        for i, interface in enumerate(interfaces, 1):
            print(f"{i}. {interface}")
        
        while True:
            try:
                choice = int(input("\nSelect network interface to configure (number): "))
                if 1 <= choice <= len(interfaces):
                    interface = interfaces[choice-1]
                    break
                else:
                    print_error("Invalid selection. Please try again.")
            except ValueError:
                print_error("Please enter a number.")
        
        # Get current connection name for the interface
        conn_name = None
        result = run_command(f"nmcli -t -f NAME,DEVICE connection show", check=False)
        for line in result.stdout.splitlines():
            if ':' in line and interface in line.split(':')[1]:
                conn_name = line.split(':')[0]
                break
        
        if not conn_name:
            print_warning(f"No connection found for interface {interface}.")
            return
        
        # Check for backup
        backup_dir = "/tmp/network-backups"
        backup_files = glob.glob(f"{backup_dir}/{conn_name.replace(' ', '_')}-*.nmconnection")
        
        if backup_files:
            # Sort by timestamp (newest first)
            backup_files.sort(reverse=True)
            backup_file = backup_files[0]
            
            print(f"Found backup file: {backup_file}")
            restore = input("Do you want to restore this backup? (y/n): ").lower()
            
            if restore == 'y':
                # Delete current connection and import backup
                run_command(f"nmcli connection delete '{conn_name}'", check=False, shell=True)
                run_command(f"nmcli connection import type nmcli file '{backup_file}'", check=False, shell=True)
                print_success(f"Restored connection from backup: {backup_file}")
                return
        
        # No backup or user declined, ask if they want to configure DHCP
        dhcp = input("Do you want to configure the network interface to use DHCP? (y/n): ").lower() == 'y'
        
        if dhcp:
            # Modify connection to use DHCP
            run_command(f"nmcli connection modify '{conn_name}' ipv4.method auto", shell=True)
            run_command(f"nmcli connection modify '{conn_name}' ipv4.addresses ''", shell=True)
            run_command(f"nmcli connection modify '{conn_name}' ipv4.gateway ''", shell=True)
            run_command(f"nmcli connection modify '{conn_name}' ipv4.dns ''", shell=True)
            run_command(f"nmcli connection modify '{conn_name}' ipv4.dns-search ''", shell=True)
            
            # Apply changes
            run_command(f"nmcli connection up '{conn_name}'", shell=True)
            print_success(f"Network interface {interface} configured to use DHCP")
    
    def remove_dns_zone_files(self):
        """Remove DNS zone files based on the distribution"""
        print_step("Removing DNS zone files...")
        
        if self.distro.is_debian_based:
            # Get list of custom zone files
            bind_dir = '/etc/bind'
            if not os.path.exists(bind_dir):
                print_warning("BIND9 directory not found. Skipping this step.")
                return
            
            # Look for custom zone files (not the default ones)
            default_files = ['db.0', 'db.127', 'db.255', 'db.empty', 'db.local', 'db.root', 
                            'named.conf', 'named.conf.default-zones', 'named.conf.local', 
                            'named.conf.options', 'zones.rfc1918']
            
            custom_files = []
            for file in os.listdir(bind_dir):
                if file.startswith('db.') and file not in default_files:
                    custom_files.append(os.path.join(bind_dir, file))
            
            if not custom_files:
                print_warning("No custom DNS zone files found.")
                return
            
            print("Found the following custom DNS zone files:")
            for i, file in enumerate(custom_files, 1):
                print(f"{i}. {os.path.basename(file)}")
            
            # Confirm removal
            if input("\nDo you want to remove these files? (y/n): ").lower() == 'y':
                for file in custom_files:
                    try:
                        os.remove(file)
                        print(f"Removed {os.path.basename(file)}")
                    except Exception as e:
                        print_error(f"Failed to remove {os.path.basename(file)}: {e}")
                
                print_success("Custom DNS zone files removed")
            else:
                print("Skipping removal of custom DNS zone files.")
            
            # Reset named.conf.local and named.conf.options if they exist
            if os.path.exists(f"{bind_dir}/named.conf.local"):
                with open(f"{bind_dir}/named.conf.local", 'w') as f:
                    f.write("// Empty configuration file\n")
                print_success("Reset named.conf.local")
            
            if os.path.exists(f"{bind_dir}/named.conf.options"):
                with open(f"{bind_dir}/named.conf.options", 'w') as f:
                    f.write("""options {
    directory "/var/cache/bind";
    
    // If there is a firewall between you and nameservers you want
    // to talk to, you may need to fix the firewall to allow multiple
    // ports to talk. See http://www.kb.cert.org/vuls/id/800113
    
    // If your ISP provided one or more IP addresses for stable
    // nameservers, you probably want to use them as forwarders.
    // Uncomment the following block, and insert the addresses replacing
    // the all-0's placeholder.
    
    // forwarders {
    //     0.0.0.0;
    // };
    
    //========================================================================
    // If BIND logs error messages about the root key being expired,
    // you will need to update your keys. See https://www.isc.org/bind-keys
    //========================================================================
    dnssec-validation auto;
    
    listen-on-v6 { any; };
};
""")
                print_success("Reset named.conf.options")
        
        elif self.distro.is_rhel_based:
            # Check if zone files exist
            zone_files = glob.glob("/var/named/*.zone")
            
            if not zone_files:
                print_warning("No DNS zone files found.")
                return
            
            print("Found the following DNS zone files:")
            for i, file in enumerate(zone_files, 1):
                print(f"{i}. {os.path.basename(file)}")
            
            # Confirm removal
            if input("\nDo you want to remove these files? (y/n): ").lower() == 'y':
                for file in zone_files:
                    try:
                        os.remove(file)
                        print(f"Removed {os.path.basename(file)}")
                    except Exception as e:
                        print_error(f"Failed to remove {os.path.basename(file)}: {e}")
                
                print_success("DNS zone files removed")
            else:
                print("Skipping removal of DNS zone files.")
            
            # Reset named.conf if it exists
            if os.path.exists('/etc/named.conf'):
                # Backup the file
                run_command("cp /etc/named.conf /etc/named.conf.bak", check=False)
                
                # Reset to default or remove
                if input("Do you want to reset named.conf to default? (y/n): ").lower() == 'y':
                    # Try to reinstall the default config
                    run_command("dnf reinstall -y bind-minimal", check=False)
                else:
                    # Just remove custom zones
                    with open('/etc/named.conf', 'r') as f:
                        content = f.readlines()
                    
                    with open('/etc/named.conf', 'w') as f:
                        for line in content:
                            # Skip custom zone definitions
                            if "zone" in line and ".zone" in line:
                                continue
                            f.write(line)
                    
                    print_success("Removed custom zone definitions from named.conf")
    
    def reset_hostname(self):
        """Reset hostname if needed"""
        print_step("Checking hostname...")
        
        current_hostname = run_command("hostname", check=False).stdout.strip()
        print(f"Current hostname: {current_hostname}")
        
        reset = input("Do you want to reset the hostname? (y/n): ").lower() == 'y'
        if not reset:
            print("Skipping hostname reset.")
            return
        
        new_hostname = input(f"Enter new hostname [{self.default_hostname}]: ").strip() or self.default_hostname
        
        # Set new hostname
        run_command(f"hostnamectl set-hostname {new_hostname}", check=False)
        
        # Update /etc/hosts
        with open('/etc/hosts', 'r') as f:
            hosts_content = f.readlines()
        
        with open('/etc/hosts', 'w') as f:
            for line in hosts_content:
                # Skip lines with the old hostname
                if current_hostname in line and '127.0.1.1' in line:
                    f.write(f"127.0.1.1\t{new_hostname}\n")
                else:
                    f.write(line)
        
        print_success(f"Hostname reset to {new_hostname}")
    
    def clean_up_dns_resolver(self):
        """Clean up DNS resolver configuration based on the distribution"""
        if self.distro.is_debian_based:
            self.clean_up_systemd_resolved()
        elif self.distro.is_rhel_based:
            # RHEL-based systems typically don't use systemd-resolved
            pass
    
    def clean_up_systemd_resolved(self):
        """Clean up systemd-resolved configuration (Debian-based)"""
        print_step("Cleaning up systemd-resolved configuration...")
        
        resolved_conf = '/etc/systemd/resolved.conf'
        if not os.path.exists(resolved_conf):
            print_warning("systemd-resolved configuration not found. Skipping this step.")
            return
        
        # Check if there's a backup
        backup_file = f"{resolved_conf}.bak"
        if os.path.exists(backup_file):
            # Restore from backup
            run_command(f"cp {backup_file} {resolved_conf}", check=False)
            print_success("Restored systemd-resolved configuration from backup")
        else:
            # Reset to defaults
            with open(resolved_conf, 'w') as f:
                f.write("""#  This file is part of systemd.
#
#  systemd is free software; you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 2.1 of the License, or
#  (at your option) any later version.
#
# Entries in this file show the compile time defaults.
# You can change settings by editing this file.
# Defaults can be restored by simply deleting this file.
#
# See resolved.conf(5) for details

[Resolve]
#DNS=
#FallbackDNS=
#Domains=
#LLMNR=yes
#MulticastDNS=yes
#DNSSEC=allow-downgrade
#DNSOverTLS=no
#Cache=yes
#DNSStubListener=yes
#ReadEtcHosts=yes
""")
            print_success("Reset systemd-resolved configuration to defaults")
        
        # Restart systemd-resolved
        run_command("systemctl restart systemd-resolved", check=False)
        
        # Check if /etc/resolv.conf is a symlink and fix if needed
        if os.path.islink('/etc/resolv.conf'):
            target = os.readlink('/etc/resolv.conf')
            if target == '/run/systemd/resolve/resolv.conf':
                # This is the correct symlink for systemd-resolved
                pass
            else:
                # Ask if user wants to reset the symlink
                reset_symlink = input("Do you want to reset /etc/resolv.conf to use systemd-resolved? (y/n): ").lower() == 'y'
                if reset_symlink:
                    if os.path.exists('/etc/resolv.conf'):
                        os.remove('/etc/resolv.conf')
                    os.symlink('/run/systemd/resolve/resolv.conf', '/etc/resolv.conf')
                    print_success("Reset /etc/resolv.conf to use systemd-resolved")
        else:
            # Not a symlink, ask if user wants to convert it
            convert_to_symlink = input("/etc/resolv.conf is not a symlink. Convert it to use systemd-resolved? (y/n): ").lower() == 'y'
            if convert_to_symlink:
                # Backup the current file
                run_command("cp /etc/resolv.conf /etc/resolv.conf.bak", check=False)
                os.remove('/etc/resolv.conf')
                os.symlink('/run/systemd/resolve/resolv.conf', '/etc/resolv.conf')
                print_success("Converted /etc/resolv.conf to use systemd-resolved")
    
    def uninstall_dns_server(self):
        """Uninstall DNS server"""
        # Confirm uninstallation
        self.confirm_uninstall()
        
        # Stop DNS service
        self.stop_dns_service()
        
        # Remove DNS packages
        self.remove_dns_packages()
        
        # Remove DNS zone files
        self.remove_dns_zone_files()
        
        # Clean up DNS resolver
        self.clean_up_dns_resolver()
        
        # Restore network configuration
        self.restore_network_configuration()
        
        # Reset hostname
        self.reset_hostname()
        
        print_header("DNS Server Uninstallation Complete")
        print("Your system has been restored to its previous state.")
        print("You may need to reboot for all changes to take effect.")
        
        reboot = input("\nDo you want to reboot now? (y/n): ").lower() == 'y'
        if reboot:
            print("Rebooting system...")
            time.sleep(2)
            run_command("reboot", check=False)
    

def main():
    """Main function to run the DNS server management script"""
    try:
        # Check if running as root
        check_root()
        
        # Initialize DNS server manager
        dns_manager = DNSServerManager()
        
        print_header(f"DNS Server Manager for {dns_manager.distro.name} {dns_manager.distro.version}")
        
        # Check if DNS server is already installed
        dns_installed = dns_manager.is_dns_server_installed()
        
        if dns_installed:
            print_header("DNS Server Already Installed")
            print("A DNS server appears to be already installed on this system.")
            action = input("Would you like to (u)ninstall the existing server or (r)econfigure it? (u/r): ").lower()
            
            if action == 'u':
                dns_manager.uninstall_dns_server()
            elif action == 'r':
                dns_manager.install_dns_server()
            else:
                print("Invalid option. Exiting.")
                sys.exit(0)
        else:
            print_header("DNS Server Installation")
            dns_manager.install_dns_server()
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
