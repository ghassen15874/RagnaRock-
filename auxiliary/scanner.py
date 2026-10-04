#!/usr/bin/env python3
"""
Port Scanner Auxiliary Module
"""

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from auxiliary.auxiliary_base import AuxiliaryBase

class PortScanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/portscan/tcp"
        self.description = "TCP Port Scanner"
        self.author = "PySploit Framework"
        self.references = []
        self.targets = ["Any TCP service"]
        
        self.options = {
            'RHOSTS': {'type': 'string', 'required': True, 'description': 'Target IP or range (192.168.1.1 or 192.168.1.1-100)'},
            'PORTS': {'type': 'string', 'required': False, 'default': '1-1000', 'description': 'Ports to scan (80,443 or 1-1000)'},
            'THREADS': {'type': 'int', 'required': False, 'default': 50, 'description': 'Number of threads'},
            'TIMEOUT': {'type': 'int', 'required': False, 'default': 2, 'description': 'Connection timeout in seconds'},
            'VERBOSE': {'type': 'bool', 'required': False, 'default': False, 'description': 'Show all attempts'}
        }
        
        self.open_ports = []
        self.scanned_count = 0
        self.total_ports = 0
        self._lock = threading.Lock()  # Protects open_ports and scanned_count (fixes B4)

    def get_option(self, name):
        """Safely get option value with proper type conversion"""
        if name in self.options and 'value' in self.options[name]:
            value = self.options[name]['value']
        elif 'default' in self.options[name]:
            value = self.options[name]['default']
        else:
            return None
        
        # Type conversion
        option_type = self.options[name].get('type', 'string')
        
        if option_type == 'int':
            try:
                return int(value)
            except (ValueError, TypeError):
                print(f"[!] Warning: Option {name} should be integer, using default")
                return self.options[name].get('default')
        elif option_type == 'bool':
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 'on')
            return bool(value)
        else:
            return str(value)

    def parse_ports(self, ports_string):
        """Parse port ranges like '80,443,1-1000'"""
        ports = []
        
        # Split by commas
        parts = ports_string.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Handle range like 1-1000
                start, end = part.split('-')
                try:
                    start_port = int(start)
                    end_port = int(end)
                    ports.extend(range(start_port, end_port + 1))
                except ValueError:
                    print(f"[-] Invalid port range: {part}")
            else:
                # Handle single port
                try:
                    ports.append(int(part))
                except ValueError:
                    print(f"[-] Invalid port: {part}")
        
        # Remove duplicates and sort
        return sorted(set(ports))

    def parse_hosts(self, hosts_string):
        """Parse host ranges like '192.168.1.1-100' or '192.168.1.1-192.168.1.100'"""
        hosts = []

        if '-' in hosts_string:
            base_ip, range_part = hosts_string.split('-', 1)
            ip_parts = base_ip.split('.')

            if len(ip_parts) == 4:
                try:
                    # Short form: 192.168.1.1-100 (range_part is end octet)
                    end = int(range_part)
                    start = int(ip_parts[3])
                except ValueError:
                    # Long form: 192.168.1.1-192.168.1.100
                    if '.' in range_part:
                        end_ip_parts = range_part.split('.')
                        if len(end_ip_parts) == 4:
                            try:
                                start = int(ip_parts[3])
                                end = int(end_ip_parts[3])
                            except ValueError:
                                hosts.append(hosts_string)
                                return hosts
                        else:
                            hosts.append(hosts_string)
                            return hosts
                    else:
                        hosts.append(hosts_string)
                        return hosts

                base = '.'.join(ip_parts[:3])
                for i in range(start, end + 1):
                    hosts.append(f"{base}.{i}")
            else:
                hosts.append(hosts_string)
        else:
            hosts.append(hosts_string)

        return hosts

    def scan_port(self, host, port, timeout, verbose):
        """Scan a single port (thread-safe via lock, fixes B4)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            with self._lock:
                self.scanned_count += 1

            if result == 0:
                with self._lock:
                    self.open_ports.append((host, port))
                print(f"[+] {host}:{port} - OPEN")
                return True
            else:
                if verbose:
                    print(f"[-] {host}:{port} - CLOSED")
                return False

        except Exception as e:
            if verbose:
                print(f"[-] {host}:{port} - ERROR: {e}")
            return False

    def get_service_name(self, port):
        """Get common service name for port"""
        common_services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 111: "RPC", 135: "RPC", 139: "NetBIOS",
            143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
            1433: "MSSQL", 1521: "Oracle", 1723: "PPTP", 3306: "MySQL",
            3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
            27017: "MongoDB", 8080: "HTTP-ALT", 8443: "HTTPS-ALT"
        }
        return common_services.get(port, "Unknown")

    def run(self):
        """Main scan method"""
        print("[*] Starting TCP Port Scanner...")
        
        # Get options with proper type conversion
        rhosts = self.get_option('RHOSTS')
        ports_str = self.get_option('PORTS')
        threads = self.get_option('THREADS')
        timeout = self.get_option('TIMEOUT')
        verbose = self.get_option('VERBOSE')
        
        if not rhosts:
            print("[-] RHOSTS is required")
            return False
        
        # Parse hosts and ports
        hosts = self.parse_hosts(rhosts)
        ports = self.parse_ports(ports_str)
        
        if not hosts or not ports:
            print("[-] No valid hosts or ports to scan")
            return False
        
        self.total_ports = len(hosts) * len(ports)
        
        print(f"[*] Target: {rhosts}")
        print(f"[*] Ports: {ports_str}")
        print(f"[*] Threads: {threads}")
        print(f"[*] Timeout: {timeout}s")
        print(f"[*] Total scans: {self.total_ports}")
        print("[*] Scanning...\n")
        
        start_time = time.time()
        self.open_ports = []
        self.scanned_count = 0
        
        # Validate thread count
        if threads <= 0:
            print("[-] Thread count must be positive")
            return False
        
        if threads > 500:
            print("[!] Warning: High thread count may cause system strain")
        
        # Scan using thread pool
        try:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = []
                for host in hosts:
                    for port in ports:
                        future = executor.submit(self.scan_port, host, port, timeout, verbose)
                        futures.append(future)
                
                # Wait for completion and show progress
                completed = 0
                total = len(futures)
                
                for future in futures:
                    future.result()
                    completed += 1
                    
                    # Show progress every 10%
                    if completed % max(1, total // 10) == 0 or completed == total:
                        progress = (completed / total) * 100
                        print(f"[*] Progress: {completed}/{total} ({progress:.1f}%)")
            
            # Show results
            scan_time = time.time() - start_time
            self.show_results(scan_time)
            
            return True
            
        except Exception as e:
            print(f"[-] Scan error: {e}")
            return False

    def show_results(self, scan_time):
        """Display scan results and save to database"""
        print(f"\n[*] Scan completed in {scan_time:.2f} seconds")
        print(f"[*] Scanned {self.scanned_count} ports")
        print(f"[*] Found {len(self.open_ports)} open ports\n")
        
        if self.open_ports:
            print("OPEN PORTS:")
            print("=" * 50)
            
            # Group by host
            hosts_ports = {}
            for host, port in self.open_ports:
                if host not in hosts_ports:
                    hosts_ports[host] = []
                hosts_ports[host].append(port)
            
            # Database saving logic
            db_available = hasattr(self, 'framework') and self.framework and hasattr(self.framework, 'session_manager')
            if db_available:
                db = self.framework.session_manager.db
                workspace = self.framework.session_manager.current_workspace
                print(f"[*] Saving results to workspace '{workspace}'...")
            
            for host in sorted(hosts_ports.keys()):
                print(f"\n{host}:")
                
                host_id = None
                if db_available:
                    host_id = db.add_host(workspace, host, status='alive')
                
                for port in sorted(hosts_ports[host]):
                    service = self.get_service_name(port)
                    print(f"  {port}/tcp - {service}")
                    
                    if db_available and host_id:
                        db.add_service(host_id, port, protocol='tcp', name=service, state='open')
        
        print(f"\n[+] Port scan completed")