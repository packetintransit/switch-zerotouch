#!/usr/bin/env python3

import ipaddress
import yaml
import os

class SwitchInventoryManager:
    def __init__(self, base_network='10.127.151.0/24', start_ip='10.127.151.131'):
        self.network = ipaddress.ip_network(base_network)
        self.start_ip = ipaddress.ip_address(start_ip)
        self.inventory_path = '/etc/ansible/hosts.yaml'
        self.used_ips_path = '/etc/ansible/used_ips.yaml'

    def get_used_ips(self):
        if os.path.exists(self.used_ips_path):
            with open(self.used_ips_path, 'r') as f:
                return yaml.safe_load(f) or []
        return []

    def save_used_ips(self, used_ips):
        with open(self.used_ips_path, 'w') as f:
            yaml.dump(used_ips, f)

    def allocate_ips(self, num_switches):
        used_ips = self.get_used_ips()
        new_switches = []
        current_ip = self.start_ip

        while len(new_switches) < num_switches:
            ip_str = str(current_ip)
            if ip_str not in used_ips:
                new_switches.append({
                    'hostname': f'SWITCH-{len(new_switches) + 1}',
                    'ip': ip_str,
                    'vlan': 10
                })
                used_ips.append(ip_str)
            current_ip += 1

        self.save_used_ips(used_ips)
        return new_switches

    def update_ansible_inventory(self, new_switches):
        # Read existing inventory
        if os.path.exists(self.inventory_path):
            with open(self.inventory_path, 'r') as f:
                inventory = yaml.safe_load(f) or {}
        else:
            inventory = {}

        # Add new switches to inventory
        if 'all' not in inventory:
            inventory['all'] = {'children': {}}
        
        if 'switches' not in inventory['all']['children']:
            inventory['all']['children']['switches'] = {'hosts': {}}

        for switch in new_switches:
            inventory['all']['children']['switches']['hosts'][switch['hostname']] = {
                'ansible_host': switch['ip'],
                'ansible_network_os': 'ios',
                'vlan': switch['vlan']
            }

        # Write updated inventory
        with open(self.inventory_path, 'w') as f:
            yaml.dump(inventory, f)

    def deploy_switches(self, num_switches):
        # Allocate IPs
        new_switches = self.allocate_ips(num_switches)
        
        # Update Ansible inventory
        self.update_ansible_inventory(new_switches)
        
        return new_switches

# Usage Example
if __name__ == '__main__':
    import sys
    
    # Get number of switches from command line
    num_switches = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    manager = SwitchInventoryManager()
    new_switches = manager.deploy_switches(num_switches)
    
    print("Newly Allocated Switches:")
    for switch in new_switches:
        print(f"Hostname: {switch['hostname']}, IP: {switch['ip']}")