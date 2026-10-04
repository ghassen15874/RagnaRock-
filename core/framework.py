#!/usr/bin/env python3
"""
PySploit Core Framework - Fixed Version
"""

import importlib
import os
import sys
from core.session_manager import SessionManager
from core.handlers import ReverseShellHandler, HTTPHandler
from core.config import ConfigManager

class PySploitFramework:
    def __init__(self, quiet=False):
        self.config = ConfigManager()
        self.quiet = quiet
        self.payloads = {}
        self.encoders = {}
        self.formatters = {}
        self.beacons = {}
        self.exploits = {}
        self.auxiliary = {}
        self.session_manager = SessionManager(quiet=self.quiet)
        self.handlers = {
            'reverse_shell': ReverseShellHandler(self.session_manager),
            'http': HTTPHandler(self.session_manager)
        }
        self.active_handlers = {}
        self.load_modules()
    
    def load_modules(self):
        """Dynamically load all modules with error handling"""
        # Load payloads
        self.payloads = {
            'windows': self.load_module('payloads.windows', 'WindowsPayloads'),
            'linux': self.load_module('payloads.linux', 'LinuxPayloads'),
            'web': self.load_module('payloads.web', 'WebPayloads'),
            'beacon': self.load_module('payloads.beacon', 'BeaconPayloads'),
            'android': self.load_module('payloads.android', 'AndroidPayloads'),
        }
        
        # Load encoders - only load available ones
        encoder_modules = {
            'xor': ('encoders.xor', 'XOREncoder'),
            'base64': ('encoders.base64', 'Base64Encoder'),
            'aes': ('encoders.aes', 'AESEncoder'),
            'multi': ('encoders.multi', 'MultiEncoder'),
        }
        
        self.encoders = {}
        for name, (module_path, class_name) in encoder_modules.items():
            module = self.load_module(module_path, class_name)
            if module:
                self.encoders[name] = module
        
        # Load formatters - only load available ones
        formatter_modules = {
            'exe': ('formatters.exe', 'EXEFormatter'),
            'ps1': ('formatters.ps1', 'PS1Formatter'),
            'python': ('formatters.python', 'PythonFormatter'),
            'raw': ('formatters.raw', 'RawFormatter'),
            'shellcode': ('formatters.shellcode', 'ShellcodeFormatter'),
        }
        
        self.formatters = {}
        for name, (module_path, class_name) in formatter_modules.items():
            module = self.load_module(module_path, class_name)
            if module:
                self.formatters[name] = module
        
        # Load exploits
        exploit_modules = {
            'eternalblue': ('exploits.eternalblue', 'EternalBlueExploit'),
            'sqli_rce': ('exploits.sqli_rce', 'SQLiRCEExploit'),
            'command_injection': ('exploits.command_injection', 'CommandInjectionExploit'),
            'vsftpd_234': ('exploits.vsftpd', 'VSFTPDExploit'),
            'proxyshell': ('exploits.proxyshell', 'ProxyShellExploit'),
            'log4shell': ('exploits.log4shell', 'Log4ShellExploit'),
            'bluekeep': ('exploits.bluekeep', 'BlueKeepExploit'),
            'confluence_cve_2023_22527': ('exploits.confluence_cve_2023_22527', 'ConfluenceRCEExploit')
        }
        
        self.exploits = {}
        for name, (module_path, class_name) in exploit_modules.items():
            module = self.load_module(module_path, class_name)
            if module:
                module.set_framework(self)  # ✅ ADD THIS LINE
                self.exploits[name] = module
        
        auxiliary_modules = {
            'portscan': ('auxiliary.scanner', 'PortScanner'),
            'sql_injection': ('auxiliary.web.sql_injection_scanner', 'SQLInjectionScanner'),
            'mod_sql_injection': ('auxiliary.web.mod_sql_Injection_Scanner', 'ModSQLInjectionScanner'),
            'cloudscan': ('auxiliary.cloud.infrastructure_scanner', 'CloudInfrastructureScanner'),
            'apiscan': ('auxiliary.web.api_security_scanner', 'APISecurityScanner'),
            'supplychain': ('auxiliary.supplychain.dependency_scanner', 'SupplyChainScanner'),
            'blockchain': ('auxiliary.blockchain.web3_scanner', 'BlockchainWeb3Scanner'),
            'mlsecurity': ('auxiliary.ml.model_security', 'MLModelSecurityScanner'),
            'iotscan': ('auxiliary.iot.device_scanner', 'IoTDeviceScanner'),
            'ddos_test': ('auxiliary.dos.cloudflare_bypass', 'DDoSAttackSimulator'),
            'stress_test': ('auxiliary.dos.real_stress_test', 'RealStressTester'),
            'cf_bypass': ('auxiliary.dos.advanced_cloudflare_bypass', 'AdvancedCloudflareBypass'),
            'real_cf_attack': ('auxiliary.dos.real_cf_bypass_attack', 'RealCFBypassAttack'),
        }
        
        self.auxiliary = {}
        for name, (module_path, class_name) in auxiliary_modules.items():
            module = self.load_module(module_path, class_name)
            if module:
                if hasattr(module, 'set_framework'):
                    module.set_framework(self)
                self.auxiliary[name] = module
        
        if not self.quiet:
            print(f"[+] Loaded {len(self.encoders)} encoders, {len(self.formatters)} formatters, {len(self.exploits)} exploits, {len(self.auxiliary)} auxiliary")
    
    def load_module(self, module_path, class_name):
        """Dynamically load a module class with proper error handling"""
        try:
            module = importlib.import_module(module_path)
            class_obj = getattr(module, class_name)
            return class_obj()
        except (ImportError, AttributeError) as e:
            if not self.quiet:
                print(f"[-] Failed to load {module_path}.{class_name}: {e}")
            return None
        except Exception as e:
            if not self.quiet:
                print(f"[-] Unexpected error loading {module_path}.{class_name}: {e}")
            return None
    
    def list_payloads(self):
        """List all available payloads"""
        print("\nAvailable Payloads:")
        print("=" * 50)
        for category, module in self.payloads.items():
            if module:
                print(f"\n{category.upper()}:")
                methods = [method for method in dir(module) 
                          if not method.startswith('_') and callable(getattr(module, method))]
                for method in methods:
                    print(f"  {category}/{method}")
            else:
                print(f"\n{category.upper()}: [NOT LOADED]")
    
    def list_encoders(self):
        """List all available encoders"""
        print("\nAvailable Encoders:")
        print("=" * 50)
        if self.encoders:
            for name, encoder in self.encoders.items():
                print(f"  {name} - {encoder.name if hasattr(encoder, 'name') else 'Encoder'}")
        else:
            print("  No encoders available")
    
    def list_formatters(self):
        """List all available formatters"""
        print("\nAvailable Formatters:")
        print("=" * 50)
        if self.formatters:
            for name, formatter in self.formatters.items():
                print(f"  {name} - {formatter.name if hasattr(formatter, 'name') else 'Formatter'}")
        else:
            print("  No formatters available")
    def list_exploits(self):
        """List all available exploits"""
        print("\nAvailable Exploits:")
        print("=" * 50)
        if self.exploits:
            for name, exploit in self.exploits.items():
                print(f"  {name} - {exploit.description}")
        else:
            print("  No exploits available")
    
    # All module loading (exploits, auxiliary, payloads, encoders, formatters)
    # is handled by load_modules() above. There is no separate load_exploits().

    def list_auxiliary(self):
        """List all available auxiliary modules"""
        print("\nAvailable Auxiliary Modules:")
        print("=" * 50)
        if self.auxiliary:
            for name, module in self.auxiliary.items():
                print(f"  {name} - {module.description}")
        else:
            print("  No auxiliary modules available")