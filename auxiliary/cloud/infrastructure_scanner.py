#!/usr/bin/env python3
"""
Cloud Infrastructure Scanner
Advanced cloud resource discovery and misconfiguration detection
"""

import requests
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from auxiliary.auxiliary_base import AuxiliaryBase

class CloudInfrastructureScanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/cloud/infrastructure"
        self.description = "Cloud Infrastructure Discovery & Misconfiguration Scanner"
        self.author = "PySploit Framework"
        
        self.options = {
            'TARGET': {'type': 'string', 'required': True, 'description': 'Domain or company name to target'},
            'CLOUD_PROVIDERS': {'type': 'string', 'required': False, 'default': 'aws,azure,gcp', 'description': 'Cloud providers to check (aws,azure,gcp,digitalocean)'},
            'SCAN_TYPES': {'type': 'string', 'required': False, 'default': 'buckets,containers,databases', 'description': 'Resource types to scan'},
            'THREADS': {'type': 'int', 'required': False, 'default': 10, 'description': 'Number of threads'},
            'TIMEOUT': {'type': 'int', 'required': False, 'default': 5, 'description': 'Request timeout'}
        }
        
        self.results = {
            'exposed_buckets': [],
            'misconfigured_resources': [],
            'public_databases': [],
            'leaked_credentials': []
        }

    def run(self):
        target = self.get_option('TARGET')
        providers = self.get_option('CLOUD_PROVIDERS').split(',')
        scan_types = self.get_option('SCAN_TYPES').split(',')
        threads = self.get_option('THREADS')
        timeout = self.get_option('TIMEOUT')
        
        print(f"[*] Starting Cloud Infrastructure Scan")
        print(f"[*] Target: {target}")
        print(f"[*] Providers: {', '.join(providers)}")
        print(f"[*] Scan Types: {', '.join(scan_types)}")
        print("[*] Scanning...\n")
        
        # AWS S3 Bucket Discovery
        if 'aws' in providers and 'buckets' in scan_types:
            self.scan_aws_buckets(target, threads, timeout)
        
        # Azure Storage Discovery
        if 'azure' in providers and 'containers' in scan_types:
            self.scan_azure_containers(target, threads, timeout)
        
        # GCP Storage Discovery
        if 'gcp' in providers and 'buckets' in scan_types:
            self.scan_gcp_buckets(target, threads, timeout)
        
        # Database Discovery
        if 'databases' in scan_types:
            self.scan_public_databases(target, threads, timeout)
        
        self.show_results()
        return True

    def scan_aws_buckets(self, target, threads, timeout):
        """Scan for exposed AWS S3 buckets"""
        print("[*] Scanning for AWS S3 buckets...")
        
        bucket_names = self.generate_bucket_names(target)
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for bucket in bucket_names:
                executor.submit(self.check_aws_bucket, bucket, timeout)

    def generate_bucket_names(self, target):
        """Generate potential S3 bucket names"""
        names = []
        domain_parts = target.replace('.', '-').split('-')
        
        # Common naming patterns
        patterns = [
            f"{target}",
            f"www-{target}",
            f"prod-{target}",
            f"staging-{target}",
            f"dev-{target}",
            f"test-{target}",
            f"assets-{target}",
            f"media-{target}",
            f"backup-{target}",
            f"log-{target}",
        ]
        
        # Add domain part variations
        for part in domain_parts:
            if len(part) > 2:
                patterns.extend([
                    f"{part}-assets",
                    f"{part}-media",
                    f"{part}-backup",
                    f"{part}-prod",
                ])
        
        return list(set(patterns))

    def check_aws_bucket(self, bucket_name, timeout):
        """Check if S3 bucket exists and is accessible"""
        urls = [
            f"https://{bucket_name}.s3.amazonaws.com",
            f"http://{bucket_name}.s3.amazonaws.com",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    self.results['exposed_buckets'].append({
                        'provider': 'AWS',
                        'bucket': bucket_name,
                        'url': url,
                        'access': 'Public Read',
                        'size': len(response.content) if response.content else 0
                    })
                    print(f"[+] Exposed AWS S3 Bucket: {url}")
                    
                elif response.status_code == 403:
                    self.results['misconfigured_resources'].append({
                        'provider': 'AWS',
                        'resource': bucket_name,
                        'type': 'S3 Bucket',
                        'issue': 'Exists but access denied'
                    })
                    print(f"[!] Restricted AWS S3 Bucket: {bucket_name}")
                    
            except requests.exceptions.RequestException:
                pass

    def scan_azure_containers(self, target, threads, timeout):
        """Scan for Azure storage containers"""
        print("[*] Scanning for Azure Storage Containers...")
        
        # Similar pattern generation as AWS
        container_names = self.generate_container_names(target)
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for container in container_names:
                executor.submit(self.check_azure_container, container, timeout)

    def generate_container_names(self, target):
        """Generate potential Azure container names"""
        names = []
        domain_parts = target.replace('.', '-').split('-')
        
        patterns = [
            f"{target}",
            f"www{target}",
            f"prod{target}",
            f"storage{target}",
        ]
        
        return list(set(patterns))

    def check_azure_container(self, container_name, timeout):
        """Check Azure storage container"""
        urls = [
            f"https://{container_name}.blob.core.windows.net/",
            f"https://{container_name}.file.core.windows.net/",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=timeout, verify=False)
                
                if response.status_code in [200, 404]:
                    # Azure returns 404 for non-existent, 200 for existent
                    pass
                    
            except requests.exceptions.RequestException:
                pass

    def scan_gcp_buckets(self, target, threads, timeout):
        """Scan for GCP storage buckets"""
        print("[*] Scanning for GCP Storage Buckets...")
        
        bucket_names = self.generate_gcp_bucket_names(target)
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for bucket in bucket_names:
                executor.submit(self.check_gcp_bucket, bucket, timeout)

    def generate_gcp_bucket_names(self, target):
        """Generate potential GCP bucket names"""
        return self.generate_bucket_names(target)  # Reuse AWS pattern

    def check_gcp_bucket(self, bucket_name, timeout):
        """Check GCP storage bucket"""
        urls = [
            f"https://storage.googleapis.com/{bucket_name}",
            f"https://{bucket_name}.storage.googleapis.com",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    self.results['exposed_buckets'].append({
                        'provider': 'GCP',
                        'bucket': bucket_name,
                        'url': url,
                        'access': 'Public Read',
                        'size': len(response.content) if response.content else 0
                    })
                    print(f"[+] Exposed GCP Storage Bucket: {url}")
                    
            except requests.exceptions.RequestException:
                pass

    def scan_public_databases(self, target, threads, timeout):
        """Scan for publicly accessible databases"""
        print("[*] Scanning for Public Databases...")
        
        # Common database ports and services
        db_services = [
            {'port': 27017, 'type': 'MongoDB', 'name': 'mongodb'},
            {'port': 9200, 'type': 'Elasticsearch', 'name': 'elastic'},
            {'port': 5984, 'type': 'CouchDB', 'name': 'couchdb'},
            {'port': 5432, 'type': 'PostgreSQL', 'name': 'postgres'},
            {'port': 3306, 'type': 'MySQL', 'name': 'mysql'},
        ]
        
        # This would require actual port scanning
        # For now, we'll just document the approach
        print("[*] Database scanning requires port scanning integration")
        print("[*] Consider using the portscan auxiliary module first")

    def show_results(self):
        """Display scan results"""
        print(f"\n[*] Cloud Infrastructure Scan Complete")
        print("=" * 60)
        
        if self.results['exposed_buckets']:
            print(f"\n[!] EXPOSED STORAGE BUCKETS FOUND:")
            print("-" * 40)
            for bucket in self.results['exposed_buckets']:
                print(f"  Provider: {bucket['provider']}")
                print(f"  Bucket: {bucket['bucket']}")
                print(f"  URL: {bucket['url']}")
                print(f"  Access: {bucket['access']}")
                print(f"  Size: {bucket['size']} bytes")
                print()
        
        if self.results['misconfigured_resources']:
            print(f"\n[!] MISCONFIGURED RESOURCES:")
            print("-" * 40)
            for resource in self.results['misconfigured_resources']:
                print(f"  Provider: {resource['provider']}")
                print(f"  Resource: {resource['resource']}")
                print(f"  Type: {resource['type']}")
                print(f"  Issue: {resource['issue']}")
                print()
        
        total_findings = len(self.results['exposed_buckets']) + len(self.results['misconfigured_resources'])
        print(f"[+] Scan completed. Found {total_findings} potential issues.")