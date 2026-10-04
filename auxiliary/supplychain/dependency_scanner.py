#!/usr/bin/env python3
"""
Supply Chain Dependency Scanner
Software supply chain vulnerability and dependency analysis
"""

import requests
import json
import re
from packaging import version
from auxiliary.auxiliary_base import AuxiliaryBase

class SupplyChainScanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/supplychain/dependencies"
        self.description = "Software Supply Chain Dependency Vulnerability Scanner"
        self.author = "PySploit Framework"
        
        self.options = {
            'TARGET': {'type': 'string', 'required': True, 'description': 'Git repository URL, package name, or requirements.txt file'},
            'ECOSYSTEM': {'type': 'string', 'required': False, 'default': 'npm,pypi', 'description': 'Package ecosystems to check'},
            'CHECK_TYPO_SQUATTING': {'type': 'bool', 'required': False, 'default': True, 'description': 'Check for typo-squatted packages'},
            'DEEP_ANALYSIS': {'type': 'bool', 'required': False, 'default': True, 'description': 'Analyze transitive dependencies'},
            'TIMEOUT': {'type': 'int', 'required': False, 'default': 10, 'description': 'Request timeout'}
        }
        
        self.vulnerabilities = []
        self.suspicious_packages = []

    def run(self):
        target = self.get_option('TARGET')
        ecosystems = self.get_option('ECOSYSTEM').split(',')
        check_typos = self.get_option('CHECK_TYPO_SQUATTING')
        deep_analysis = self.get_option('DEEP_ANALYSIS')
        timeout = self.get_option('TIMEOUT')
        
        print(f"[*] Starting Supply Chain Dependency Scan")
        print(f"[*] Target: {target}")
        print(f"[*] Ecosystems: {', '.join(ecosystems)}")
        print(f"[*] Typo-squatting Check: {check_typos}")
        print(f"[*] Deep Analysis: {deep_analysis}")
        print("[*] Scanning...\n")
        
        # Determine target type and process accordingly
        if target.endswith('.txt') or 'requirements' in target.lower():
            self.scan_requirements_file(target, ecosystems, timeout)
        elif 'github.com' in target or 'gitlab.com' in target:
            self.scan_repository(target, ecosystems, timeout)
        else:
            # Assume it's a package name
            for ecosystem in ecosystems:
                self.scan_package(ecosystem, target, timeout)
        
        if check_typos:
            self.check_typo_squatting(target, ecosystems, timeout)
        
        self.show_results()
        return True

    def scan_requirements_file(self, file_path, ecosystems, timeout):
        """Scan a requirements.txt or package.json file"""
        print(f"[*] Scanning dependencies file: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Python requirements.txt
            if 'pypi' in ecosystems:
                self.scan_python_requirements(content, timeout)
            
            # TODO: Add npm package.json support
            # TODO: Add Ruby Gemfile support
            
        except FileNotFoundError:
            print(f"[-] File not found: {file_path}")
        except Exception as e:
            print(f"[-] Error reading file: {e}")

    def scan_python_requirements(self, content, timeout):
        """Scan Python requirements for vulnerabilities"""
        print("[*] Scanning Python dependencies...")
        
        # Parse requirements.txt format
        lines = content.split('\n')
        packages = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle different requirement formats
                package = re.split(r'[=<>!]', line)[0].strip()
                if package:
                    packages.append(package)
        
        for package in packages:
            self.check_pypi_package(package, timeout)

    def check_pypi_package(self, package_name, timeout):
        """Check a PyPI package for known vulnerabilities"""
        try:
            # Check PyPI API for package info
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data['info']['version']
                
                print(f"[*] Checking {package_name} ({latest_version})")
                
                # Check for known vulnerabilities (simplified)
                # In real implementation, integrate with OSV database
                vuln_check = self.check_known_vulnerabilities(package_name, latest_version)
                
                if vuln_check['vulnerable']:
                    self.vulnerabilities.append({
                        'package': package_name,
                        'version': latest_version,
                        'ecosystem': 'pypi',
                        'vulnerability': vuln_check['description'],
                        'severity': vuln_check['severity']
                    })
                    print(f"[-] VULNERABLE: {package_name} - {vuln_check['description']}")
                else:
                    print(f"[+] Secure: {package_name}")
            
            else:
                print(f"[-] Package not found: {package_name}")
                
        except requests.exceptions.RequestException as e:
            print(f"[-] Error checking {package_name}: {e}")

    def check_known_vulnerabilities(self, package, version):
        """Check for known vulnerabilities (placeholder implementation)"""
        # This would integrate with OSV database or similar
        # For demo purposes, we'll use a simple hardcoded list
        
        known_vulns = {
            'django': {
                'versions': ['<2.2.0', '>=3.0.0,<3.0.1'],
                'description': 'Potential SQL injection vulnerability',
                'severity': 'high'
            },
            'requests': {
                'versions': ['<2.20.0'],
                'description': 'SSRF vulnerability',
                'severity': 'medium'
            },
            'flask': {
                'versions': ['<1.0.0'],
                'description': 'XSS vulnerability in debugger',
                'severity': 'medium'
            }
        }
        
        if package.lower() in known_vulns:
            vuln_info = known_vulns[package.lower()]
            # Simplified version check - in real implementation use proper version comparison
            if any(v in version for v in ['0.', '1.0', '2.0']):  # Simplified check
                return {
                    'vulnerable': True,
                    'description': vuln_info['description'],
                    'severity': vuln_info['severity']
                }
        
        return {'vulnerable': False}

    def scan_repository(self, repo_url, ecosystems, timeout):
        """Scan a Git repository for dependency files"""
        print(f"[*] Scanning repository: {repo_url}")
        
        # Extract owner and repo name from URL
        match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
        if match:
            owner, repo = match.groups()
            
            # Check for common dependency files
            files_to_check = [
                'requirements.txt', 'package.json', 'Gemfile',
                'pom.xml', 'build.gradle', 'go.mod'
            ]
            
            for file in files_to_check:
                self.check_repo_file(owner, repo, file, ecosystems, timeout)
        else:
            print(f"[-] Could not parse repository URL: {repo_url}")

    def check_repo_file(self, owner, repo, filename, ecosystems, timeout):
        """Check if a dependency file exists in the repository"""
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{filename}"
        
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                print(f"[+] Found {filename} in repository")
                # Process the file based on its type
                if filename == 'requirements.txt' and 'pypi' in ecosystems:
                    self.scan_python_requirements(response.text, timeout)
                # Add handlers for other file types
                
        except requests.exceptions.RequestException:
            pass

    def check_typo_squatting(self, target, ecosystems, timeout):
        """Check for typo-squatted package names"""
        print("[*] Checking for typo-squatted packages...")
        
        if 'pypi' in ecosystems:
            self.check_pypi_typos(target, timeout)

    def check_pypi_typos(self, package_name, timeout):
        """Check for typo-squatted PyPI packages"""
        common_typos = self.generate_typos(package_name)
        
        for typo in common_typos:
            try:
                url = f"https://pypi.org/pypi/{typo}/json"
                response = requests.get(url, timeout=timeout)
                
                if response.status_code == 200:
                    self.suspicious_packages.append({
                        'original': package_name,
                        'squatting': typo,
                        'ecosystem': 'pypi',
                        'description': 'Potential typo-squatting'
                    })
                    print(f"[!] Potential typo-squatting: {typo} (original: {package_name})")
                    
            except requests.exceptions.RequestException:
                pass

    def generate_typos(self, word):
        """Generate common typos for a word"""
        typos = []
        
        # Common typing mistakes
        for i in range(len(word)):
            # Character omission
            if i > 0:
                typos.append(word[:i] + word[i+1:])
            
            # Character duplication
            typos.append(word[:i] + word[i] + word[i:])
            
            # Adjacent character swap (QWERTY keyboard)
            if i < len(word) - 1:
                typos.append(word[:i] + word[i+1] + word[i] + word[i+2:])
        
        # Common substitutions
        substitutions = {
            'o': '0', 'i': '1', 'l': '1', 'e': '3',
            'a': '4', 's': '5', 't': '7', 'b': '8',
            'g': '9', '0': 'o', '1': 'l', '3': 'e'
        }
        
        for char, sub in substitutions.items():
            if char in word:
                typos.append(word.replace(char, sub))
        
        return list(set(typos))[:10]  # Limit to 10 variations

    def show_results(self):
        """Display scan results"""
        print(f"\n[*] Supply Chain Dependency Scan Complete")
        print("=" * 60)
        
        if self.vulnerabilities:
            print(f"\n[!] VULNERABLE DEPENDENCIES FOUND ({len(self.vulnerabilities)}):")
            print("-" * 40)
            for vuln in self.vulnerabilities:
                print(f"  Package: {vuln['package']}")
                print(f"  Version: {vuln['version']}")
                print(f"  Ecosystem: {vuln['ecosystem']}")
                print(f"  Issue: {vuln['vulnerability']}")
                print(f"  Severity: {vuln['severity']}")
                print()
        
        if self.suspicious_packages:
            print(f"\n[!] SUSPICIOUS PACKAGES ({len(self.suspicious_packages)}):")
            print("-" * 40)
            for pkg in self.suspicious_packages:
                print(f"  Original: {pkg['original']}")
                print(f"  Suspicious: {pkg['squatting']}")
                print(f"  Ecosystem: {pkg['ecosystem']}")
                print(f"  Description: {pkg['description']}")
                print()
        
        total_issues = len(self.vulnerabilities) + len(self.suspicious_packages)
        print(f"[+] Scan completed. Found {total_issues} potential supply chain issues.")