#!/usr/bin/env python3
"""
IoT Device Fingerprinter
Advanced IoT device discovery and vulnerability assessment
"""

import socket
import requests
import json
import threading
import paho.mqtt.client as mqtt

from concurrent.futures import ThreadPoolExecutor
from auxiliary.auxiliary_base import AuxiliaryBase

class IoTDeviceScanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/iot/discovery"
        self.description = "IoT Device Discovery & Vulnerability Assessment"
        self.author = "PySploit Framework"
        
        self.options = {
            'TARGET_RANGE': {'type': 'string', 'required': True, 'description': 'IP range to scan (192.168.1.0/24 or 192.168.1.1-100)'},
            'PROTOCOLS': {'type': 'string', 'required': False, 'default': 'mqtt,coap,upnp,ssdp', 'description': 'IoT protocols to scan'},
            'CHECK_DEFAULT_CREDS': {'type': 'bool', 'required': False, 'default': True, 'description': 'Test default credentials'},
            'FIRMWARE_ANALYSIS': {'type': 'bool', 'required': False, 'default': False, 'description': 'Attempt firmware analysis'},
            'THREADS': {'type': 'int', 'required': False, 'default': 20, 'description': 'Number of threads'},
            'TIMEOUT': {'type': 'int', 'required': False, 'default': 3, 'description': 'Connection timeout'}
        }
        
        self.discovered_devices = []
        self.vulnerabilities = []

    def run(self):
        target_range = self.get_option('TARGET_RANGE')
        protocols = self.get_option('PROTOCOLS').split(',')
        check_creds = self.get_option('CHECK_DEFAULT_CREDS')
        firmware_analysis = self.get_option('FIRMWARE_ANALYSIS')
        threads = self.get_option('THREADS')
        timeout = self.get_option('TIMEOUT')
        
        print(f"[*] Starting IoT Device Discovery Scan")
        print(f"[*] Target Range: {target_range}")
        print(f"[*] Protocols: {', '.join(protocols)}")
        print(f"[*] Default Credentials: {check_creds}")
        print(f"[*] Firmware Analysis: {firmware_analysis}")
        print("[*] Scanning...\n")
        
        # Generate IP list from target range
        ip_list = self.parse_ip_range(target_range)
        if not ip_list:
            print("[-] Invalid target range")
            return False
        
        print(f"[*] Scanning {len(ip_list)} IP addresses")
        
        # Protocol-specific scanning
        for protocol in protocols:
            if protocol == 'mqtt':
                self.scan_mqtt_devices(ip_list, threads, timeout)
            elif protocol == 'coap':
                self.scan_coap_devices(ip_list, threads, timeout)
            elif protocol == 'upnp':
                self.scan_upnp_devices(ip_list, threads, timeout)
            elif protocol == 'ssdp':
                self.scan_ssdp_devices(ip_list, threads, timeout)
        
        # Default credential testing
        if check_creds:
            self.test_default_credentials(threads, timeout)
        
        # Firmware analysis
        if firmware_analysis:
            self.attempt_firmware_analysis()
        
        self.show_results()
        return True

    def parse_ip_range(self, target_range):
        """Parse IP range into list of individual IPs"""
        ip_list = []
        
        if '/' in target_range:
            # CIDR notation
            return self.cidr_to_ips(target_range)
        elif '-' in target_range:
            # Range notation (192.168.1.1-100)
            base_ip, range_part = target_range.split('-')
            ip_parts = base_ip.split('.')
            
            if len(ip_parts) == 4:
                try:
                    start = int(ip_parts[3])
                    end = int(range_part)
                    base = '.'.join(ip_parts[:3])
                    
                    for i in range(start, end + 1):
                        ip_list.append(f"{base}.{i}")
                except ValueError:
                    print(f"[-] Invalid IP range: {target_range}")
        else:
            # Single IP
            ip_list.append(target_range)
        
        return ip_list

    def cidr_to_ips(self, cidr):
        """Convert CIDR notation to IP list (simplified)"""
        # For demo, return a small subset
        base_ip = cidr.split('/')[0]
        ip_parts = base_ip.split('.')
        
        if len(ip_parts) == 4:
            return [f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{i}" for i in range(1, 11)]
        
        return []

    def scan_mqtt_devices(self, ip_list, threads, timeout):
        """Scan for MQTT brokers"""
        print("[*] Scanning for MQTT brokers...")
        
        mqtt_port = 1883
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for ip in ip_list:
                executor.submit(self.check_mqtt_broker, ip, mqtt_port, timeout)

    def check_mqtt_broker(self, ip, port, timeout):
        """Check if MQTT broker is running"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                device_info = {
                    'ip': ip,
                    'protocol': 'MQTT',
                    'port': port,
                    'service': 'Message Broker',
                    'status': 'Active'
                }
                self.discovered_devices.append(device_info)
                print(f"[+] MQTT Broker: {ip}:{port}")
                
                # Check for common MQTT vulnerabilities
                self.check_mqtt_vulnerabilities(ip, port)
                
        except Exception as e:
            pass

    def check_mqtt_vulnerabilities(self, ip, port):
        """Check for common MQTT security issues"""
        # Check for anonymous access
        try:
            client = mqtt.Client()
            client.connect(ip, port, 5)
            
            # If connection succeeds without credentials
            self.vulnerabilities.append({
                'device': ip,
                'protocol': 'MQTT',
                'type': 'Anonymous Access',
                'severity': 'High',
                'description': 'MQTT broker allows anonymous connections'
            })
            print(f"[-] MQTT Anonymous Access: {ip}")
            
        except Exception:
            # Connection failed or requires auth - this is good
            pass

    def scan_coap_devices(self, ip_list, threads, timeout):
        """Scan for CoAP devices"""
        print("[*] Scanning for CoAP devices...")
        
        coap_port = 5683
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for ip in ip_list:
                executor.submit(self.check_coap_device, ip, coap_port, timeout)

    def check_coap_device(self, ip, port, timeout):
        """Check if CoAP device is accessible"""
        try:
            # CoAP uses UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Simple CoAP ping (empty CON message)
            coap_ping = bytes([0x40, 0x00, 0x00, 0x00])  # CON, MID=0
            sock.sendto(coap_ping, (ip, port))
            
            try:
                data, addr = sock.recvfrom(1024)
                if data:
                    device_info = {
                        'ip': ip,
                        'protocol': 'CoAP',
                        'port': port,
                        'service': 'Constrained Application Protocol',
                        'status': 'Active'
                    }
                    self.discovered_devices.append(device_info)
                    print(f"[+] CoAP Device: {ip}:{port}")
            except socket.timeout:
                # No response - device might still be there but not responding to ping
                pass
                
            sock.close()
            
        except Exception as e:
            pass

    def scan_upnp_devices(self, ip_list, threads, timeout):
        """Scan for UPnP devices"""
        print("[*] Scanning for UPnP devices...")
        
        upnp_port = 1900
        
        # UPnP uses multicast discovery
        multicast_msg = (
            'M-SEARCH * HTTP/1.1\r\n'
            'HOST: 239.255.255.250:1900\r\n'
            'MAN: "ssdp:discover"\r\n'
            'MX: 1\r\n'
            'ST: ssdp:all\r\n\r\n'
        )
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(multicast_msg.encode(), ('239.255.255.250', upnp_port))
            
            try:
                while True:
                    data, addr = sock.recvfrom(1024)
                    ip = addr[0]
                    
                    device_info = {
                        'ip': ip,
                        'protocol': 'UPnP',
                        'port': upnp_port,
                        'service': 'Universal Plug and Play',
                        'status': 'Active',
                        'response': data.decode('utf-8', errors='ignore')[:200]
                    }
                    self.discovered_devices.append(device_info)
                    print(f"[+] UPnP Device: {ip}")
                    
            except socket.timeout:
                pass
                
            sock.close()
            
        except Exception as e:
            print(f"[-] UPnP scan error: {e}")

    def scan_ssdp_devices(self, ip_list, threads, timeout):
        """Scan for SSDP devices"""
        print("[*] Scanning for SSDP devices...")
        
        # SSDP is similar to UPnP
        self.scan_upnp_devices(ip_list, threads, timeout)

    def test_default_credentials(self, threads, timeout):
        """Test discovered devices for default credentials"""
        print("[*] Testing default credentials...")
        
        common_credentials = [
            ('admin', 'admin'),
            ('admin', 'password'),
            ('root', 'root'),
            ('root', 'password'),
            ('user', 'user'),
            ('admin', '1234'),
            ('admin', ''),
        ]
        
        # Test web interfaces
        for device in self.discovered_devices:
            if device['protocol'] in ['HTTP', 'HTTPS'] or device['port'] in [80, 443, 8080]:
                for username, password in common_credentials[:3]:  # Limit for demo
                    self.test_http_auth(device['ip'], device.get('port', 80), username, password, timeout)

    def test_http_auth(self, ip, port, username, password, timeout):
        """Test HTTP authentication"""
        try:
            url = f"http://{ip}:{port}"
            response = requests.get(url, auth=(username, password), timeout=timeout, verify=False)
            
            if response.status_code == 200:
                self.vulnerabilities.append({
                    'device': ip,
                    'protocol': 'HTTP',
                    'type': 'Default Credentials',
                    'severity': 'Critical',
                    'description': f'Default credentials work: {username}:{password}'
                })
                print(f"[-] DEFAULT CREDENTIALS: {ip} - {username}:{password}")
                
        except Exception:
            pass

    def attempt_firmware_analysis(self):
        """Attempt to analyze device firmware"""
        print("[*] Attempting firmware analysis...")
        
        # This would involve:
        # 1. Downloading firmware from device
        # 2. Extracting and analyzing files
        # 3. Checking for known vulnerabilities
        
        print("[*] Firmware analysis requires device-specific access")
        print("[*] Consider manual analysis for critical devices")

    def show_results(self):
        """Display scan results"""
        print(f"\n[*] IoT Device Discovery Scan Complete")
        print("=" * 60)
        
        if self.discovered_devices:
            print(f"\n[+] DEVICES DISCOVERED ({len(self.discovered_devices)}):")
            print("-" * 40)
            for device in self.discovered_devices:
                print(f"  IP: {device['ip']}")
                print(f"  Protocol: {device['protocol']}")
                print(f"  Port: {device.get('port', 'N/A')}")
                print(f"  Service: {device.get('service', 'Unknown')}")
                print(f"  Status: {device.get('status', 'Unknown')}")
                if 'response' in device:
                    print(f"  Response: {device['response'][:100]}...")
                print()
        
        if self.vulnerabilities:
            print(f"\n[!] VULNERABILITIES FOUND ({len(self.vulnerabilities)}):")
            print("-" * 40)
            for vuln in self.vulnerabilities:
                print(f"  Device: {vuln['device']}")
                print(f"  Protocol: {vuln['protocol']}")
                print(f"  Type: {vuln['type']}")
                print(f"  Severity: {vuln['severity']}")
                print(f"  Description: {vuln['description']}")
                print()
        
        print(f"[+] Scan completed. Found {len(self.discovered_devices)} devices and {len(self.vulnerabilities)} vulnerabilities.")