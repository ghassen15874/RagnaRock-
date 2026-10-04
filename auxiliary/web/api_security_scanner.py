#!/usr/bin/env python3
"""
API Security Scanner
Advanced API endpoint discovery and security testing
"""

import requests
import json
import re
from urllib.parse import urljoin, urlparse
from auxiliary.auxiliary_base import AuxiliaryBase

class APISecurityScanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/web/api_security"
        self.description = "Advanced API Endpoint Discovery & Security Testing"
        self.author = "PySploit Framework"
        
        self.options = {
            'TARGET': {'type': 'string', 'required': True, 'description': 'Base URL or API endpoint'},
            'SWAGGER_SCAN': {'type': 'bool', 'required': False, 'default': True, 'description': 'Check for Swagger/OpenAPI docs'},
            'FUZZ_ENDPOINTS': {'type': 'bool', 'required': False, 'default': True, 'description': 'Fuzz for hidden endpoints'},
            'TEST_AUTH': {'type': 'bool', 'required': False, 'default': True, 'description': 'Test authentication bypasses'},
            'TIMEOUT': {'type': 'int', 'required': False, 'default': 5, 'description': 'Request timeout'},
            'WORDLIST': {'type': 'string', 'required': False, 'default': 'small', 'description': 'Wordlist size (small,medium,large)'}
        }
        
        self.discovered_endpoints = []
        self.vulnerabilities = []

    def run(self):
        target = self.get_option('TARGET')
        swagger_scan = self.get_option('SWAGGER_SCAN')
        fuzz_endpoints = self.get_option('FUZZ_ENDPOINTS')
        test_auth = self.get_option('TEST_AUTH')
        timeout = self.get_option('TIMEOUT')
        
        print(f"[*] Starting API Security Scanner")
        print(f"[*] Target: {target}")
        print(f"[*] Swagger Scan: {swagger_scan}")
        print(f"[*] Endpoint Fuzzing: {fuzz_endpoints}")
        print(f"[*] Auth Testing: {test_auth}")
        print("[*] Scanning...\n")
        
        # Normalize target URL
        if not target.startswith(('http://', 'https://')):
            target = f"https://{target}"
        
        # 1. Swagger/OpenAPI Documentation Discovery
        if swagger_scan:
            self.scan_swagger_docs(target, timeout)
        
        # 2. Endpoint Fuzzing
        if fuzz_endpoints:
            self.fuzz_endpoints(target, timeout)
        
        # 3. Authentication Testing
        if test_auth:
            self.test_authentication(target, timeout)
        
        # 4. JavaScript Analysis for API endpoints
            self.analyze_javascript_files(target, timeout)
        
        self.show_results()
        return True

    def scan_swagger_docs(self, target, timeout):
        """Check for Swagger/OpenAPI documentation"""
        print("[*] Scanning for API documentation...")
        
        common_paths = [
            '/swagger.json',
            '/swagger.yaml',
            '/swagger.yml',
            '/api/swagger.json',
            '/api/docs',
            '/docs',
            '/openapi.json',
            '/openapi.yaml',
            '/openapi.yml',
            '/v2/api-docs',
            '/v3/api-docs',
            '/api/v1/documentation',
        ]
        
        for path in common_paths:
            url = urljoin(target, path)
            try:
                response = requests.get(url, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if any(term in content_type.lower() for term in ['json', 'yaml', 'yaml']) or \
                       any(term in response.text.lower() for term in ['swagger', 'openapi']):
                        
                        self.discovered_endpoints.append({
                            'url': url,
                            'type': 'API Documentation',
                            'method': 'GET',
                            'status': response.status_code,
                            'size': len(response.text)
                        })
                        print(f"[+] Found API Documentation: {url}")
                        
            except requests.exceptions.RequestException:
                pass

    def fuzz_endpoints(self, target, timeout):
        """Fuzz for common API endpoints"""
        print("[*] Fuzzing API endpoints...")
        
        # Common API endpoint patterns
        endpoints = [
            '/api/v1/users', '/api/v1/admin', '/api/v1/config',
            '/api/users', '/api/admin', '/api/config',
            '/v1/users', '/v1/admin', '/v1/config',
            '/graphql', '/graphiql', '/playground',
            '/api/graphql', '/api/graphiql',
            '/rest', '/api/rest',
            '/jsonrpc', '/api/jsonrpc',
            '/oauth', '/auth', '/token',
            '/login', '/register', '/signup',
            '/password/reset', '/forgot-password',
            '/health', '/status', '/metrics',
            '/debug', '/api/debug',
        ]
        
        for endpoint in endpoints:
            url = urljoin(target, endpoint)
            for method in ['GET', 'POST', 'PUT', 'DELETE']:
                try:
                    if method == 'GET':
                        response = requests.get(url, timeout=timeout, verify=False)
                    elif method == 'POST':
                        response = requests.post(url, timeout=timeout, verify=False)
                    else:
                        continue
                    
                    if response.status_code not in [404, 403, 500]:
                        self.discovered_endpoints.append({
                            'url': url,
                            'type': 'API Endpoint',
                            'method': method,
                            'status': response.status_code,
                            'size': len(response.text)
                        })
                        
                        if response.status_code == 200:
                            print(f"[+] Found API Endpoint: {method} {url} ({response.status_code})")
                        else:
                            print(f"[!] Interesting Response: {method} {url} ({response.status_code})")
                            
                except requests.exceptions.RequestException:
                    pass

    def test_authentication(self, target, timeout):
        """Test for authentication bypass vulnerabilities"""
        print("[*] Testing authentication mechanisms...")
        
        # Test for IDOR-like patterns
        test_endpoints = [
            '/api/v1/users/1',
            '/api/users/1',
            '/api/v1/admin/1',
            '/api/admin/1',
        ]
        
        for endpoint in test_endpoints:
            url = urljoin(target, endpoint)
            try:
                response = requests.get(url, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    # Check if response contains user data
                    if any(field in response.text.lower() for field in ['email', 'username', 'password', 'name']):
                        self.vulnerabilities.append({
                            'type': 'IDOR',
                            'endpoint': url,
                            'method': 'GET',
                            'description': 'Potential Insecure Direct Object Reference'
                        })
                        print(f"[!] Potential IDOR vulnerability: {url}")
                        
            except requests.exceptions.RequestException:
                pass
        
        # Test for missing authentication
        sensitive_endpoints = [
            '/api/v1/config',
            '/api/admin/users',
            '/api/debug',
        ]
        
        for endpoint in sensitive_endpoints:
            url = urljoin(target, endpoint)
            try:
                response = requests.get(url, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    self.vulnerabilities.append({
                        'type': 'Missing Authentication',
                        'endpoint': url,
                        'method': 'GET',
                        'description': 'Sensitive endpoint accessible without authentication'
                    })
                    print(f"[!] Missing authentication: {url}")
                    
            except requests.exceptions.RequestException:
                pass

    def analyze_javascript_files(self, target, timeout):
        """Extract API endpoints from JavaScript files"""
        print("[*] Analyzing JavaScript files for API endpoints...")
        
        # Common JS file patterns
        js_patterns = [
            '/static/js/', '/js/', '/assets/js/',
            '/dist/js/', '/build/js/', '/public/js/'
        ]
        
        # This would require crawling the site first
        # For demonstration, we'll check common locations
        common_js_files = [
            '/app.js', '/main.js', '/api.js',
            '/static/js/app.js', '/js/main.js'
        ]
        
        api_patterns = [
            r'fetch\(["\']([^"\']+api[^"\']+)["\']',
            r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']',
            r'\.ajax\([^)]*url:\s*["\']([^"\']+)["\']',
            r'api/v[0-9]/[^"\']+',
        ]
        
        for js_file in common_js_files:
            url = urljoin(target, js_file)
            try:
                response = requests.get(url, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    for pattern in api_patterns:
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        for match in matches:
                            if isinstance(match, tuple):
                                match = match[1]  # Get the URL part from axios patterns
                            
                            endpoint = match if match.startswith('/') else f"/{match}"
                            full_url = urljoin(target, endpoint)
                            
                            self.discovered_endpoints.append({
                                'url': full_url,
                                'type': 'JS-Discovered API',
                                'method': 'GET',
                                'status': 'Unknown',
                                'size': 0
                            })
                            print(f"[+] JS Discovered API: {full_url}")
                            
            except requests.exceptions.RequestException:
                pass

    def show_results(self):
        """Display scan results"""
        print(f"\n[*] API Security Scan Complete")
        print("=" * 60)
        
        if self.discovered_endpoints:
            print(f"\n[+] DISCOVERED ENDPOINTS ({len(self.discovered_endpoints)}):")
            print("-" * 40)
            for endpoint in self.discovered_endpoints:
                print(f"  {endpoint['method']} {endpoint['url']}")
                print(f"    Type: {endpoint['type']}")
                print(f"    Status: {endpoint['status']}")
                print(f"    Size: {endpoint['size']} bytes")
                print()
        
        if self.vulnerabilities:
            print(f"\n[!] VULNERABILITIES FOUND ({len(self.vulnerabilities)}):")
            print("-" * 40)
            for vuln in self.vulnerabilities:
                print(f"  Type: {vuln['type']}")
                print(f"  Endpoint: {vuln['endpoint']}")
                print(f"  Method: {vuln['method']}")
                print(f"  Description: {vuln['description']}")
                print()
        
        print(f"[+] Scan completed. Found {len(self.discovered_endpoints)} endpoints and {len(self.vulnerabilities)} potential vulnerabilities.")