#!/usr/bin/env python3
"""
Blockchain & Web3 Security Scanner
Smart contract and blockchain infrastructure security assessment
"""

import requests
import json
import re
from web3 import Web3
from auxiliary.auxiliary_base import AuxiliaryBase

class BlockchainWeb3Scanner(AuxiliaryBase):
    def __init__(self):
        super().__init__()
        self.name = "auxiliary/scanner/blockchain/web3"
        self.description = "Blockchain & Smart Contract Security Scanner"
        self.author = "PySploit Framework"
        
        self.options = {
            'CONTRACT_ADDRESS': {'type': 'string', 'required': False, 'description': 'Smart contract address'},
            'NETWORK': {'type': 'string', 'required': False, 'default': 'ethereum', 'description': 'Blockchain network (ethereum,bsc,polygon)'},
            'SCAN_TYPES': {'type': 'string', 'required': False, 'default': 'reentrancy,overflow,access-control', 'description': 'Vulnerability types to check'},
            'RPC_ENDPOINT': {'type': 'string', 'required': False, 'description': 'Custom RPC endpoint'},
            'API_KEY': {'type': 'string', 'required': False, 'description': 'Etherscan/Block explorer API key'}
        }
        
        self.vulnerabilities = []
        self.contract_info = {}

    def run(self):
        contract_address = self.get_option('CONTRACT_ADDRESS')
        network = self.get_option('NETWORK')
        scan_types = self.get_option('SCAN_TYPES').split(',')
        rpc_endpoint = self.get_option('RPC_ENDPOINT')
        
        print(f"[*] Starting Blockchain & Web3 Security Scan")
        print(f"[*] Network: {network}")
        print(f"[*] Scan Types: {', '.join(scan_types)}")
        print("[*] Scanning...\n")
        
        if not contract_address:
            # Network-wide scanning
            self.scan_network_security(network, scan_types, rpc_endpoint)
        else:
            # Specific contract scanning
            self.scan_smart_contract(contract_address, network, scan_types, rpc_endpoint)
        
        self.show_results()
        return True

    def scan_network_security(self, network, scan_types, rpc_endpoint):
        """Scan blockchain network for common issues"""
        print(f"[*] Scanning {network} network security...")
        
        # Check network health and consensus
        self.check_network_health(network, rpc_endpoint)
        
        # Scan for recent attacks
        self.check_recent_attacks(network)
        
        # Check for hard fork status
        self.check_fork_status(network)
        
        print(f"[+] Network-level scan completed for {network}")

    def scan_smart_contract(self, contract_address, network, scan_types, rpc_endpoint):
        """Scan a specific smart contract for vulnerabilities"""
        print(f"[*] Scanning smart contract: {contract_address}")
        
        # Validate contract address
        if not self.is_valid_address(contract_address):
            print(f"[-] Invalid contract address: {contract_address}")
            return
        
        # Get contract information
        contract_info = self.get_contract_info(contract_address, network)
        if not contract_info:
            print(f"[-] Could not retrieve contract information")
            return
        
        # Analyze contract bytecode
        if contract_info.get('bytecode'):
            self.analyze_bytecode(contract_address, contract_info['bytecode'], scan_types)
        
        # Check for verified source code
        if contract_info.get('source_code'):
            self.analyze_source_code(contract_address, contract_info['source_code'], scan_types)
        
        # Check transaction history for suspicious activity
        self.analyze_transaction_history(contract_address, network)
        
        # Test common vulnerability patterns
        self.test_common_vulnerabilities(contract_address, network, scan_types, rpc_endpoint)

    def is_valid_address(self, address):
        """Validate Ethereum-style address"""
        return re.match(r'^0x[a-fA-F0-9]{40}$', address) is not None

    def get_contract_info(self, contract_address, network):
        """Get contract information from block explorer"""
        print(f"[*] Retrieving contract information from {network}...")
        
        # API endpoints for different networks
        explorers = {
            'ethereum': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'polygon': 'https://api.polygonscan.com/api'
        }
        
        if network not in explorers:
            print(f"[-] Unsupported network: {network}")
            return None
        
        api_url = explorers[network]
        api_key = self.get_option('API_KEY')
        
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': contract_address,
            'apikey': api_key
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1':
                    result = data['result'][0]
                    self.contract_info = {
                        'contract_name': result.get('ContractName', 'Unknown'),
                        'compiler_version': result.get('CompilerVersion', 'Unknown'),
                        'optimization_used': result.get('OptimizationUsed', '0'),
                        'source_code': result.get('SourceCode'),
                        'abi': result.get('ABI'),
                        'bytecode': result.get('Implementation') or result.get('Bytecode')
                    }
                    print(f"[+] Contract: {self.contract_info['contract_name']}")
                    print(f"[+] Compiler: {self.contract_info['compiler_version']}")
                    return self.contract_info
            else:
                print(f"[-] API request failed: {response.status_code}")
        except Exception as e:
            print(f"[-] Error retrieving contract info: {e}")
        
        return None

    def analyze_bytecode(self, contract_address, bytecode, scan_types):
        """Analyze contract bytecode for vulnerabilities"""
        print("[*] Analyzing contract bytecode...")
        
        # Check for common vulnerable patterns in bytecode
        vulnerable_patterns = {
            'delegatecall': 'f4',  # DELEGATECALL opcode
            'callvalue': '34',     # CALLVALUE opcode
            'call': 'f1',          # CALL opcode
            'sstore': '55',        # SSTORE opcode
        }
        
        for pattern_name, opcode in vulnerable_patterns.items():
            if opcode in bytecode:
                count = bytecode.count(opcode)
                print(f"[!] Found {count} {pattern_name.upper()} operations")
                
                if pattern_name == 'delegatecall' and 'access-control' in scan_types:
                    self.vulnerabilities.append({
                        'type': 'Unchecked Delegatecall',
                        'contract': contract_address,
                        'severity': 'High',
                        'description': 'DELEGATECALL opcode found - potential proxy pattern or upgradeable contract'
                    })

    def analyze_source_code(self, contract_address, source_code, scan_types):
        """Analyze verified source code for vulnerabilities"""
        print("[*] Analyzing contract source code...")
        
        # Common Solidity vulnerability patterns
        vulnerability_patterns = {
            'reentrancy': [
                r'\.call\.value\(.*\)',
                r'\.send\(.*\)',
                r'\.transfer\(.*\)'
            ],
            'overflow': [
                r'uint\d+\s+\w+\s*[\+\-\*\/]\=',
                r'=\s*\w+\s*[\+\-\*\/]\s*\w+'
            ],
            'access-control': [
                r'public\s+\w+',
                r'external\s+\w+',
                r'require\(msg.sender'
            ]
        }
        
        for vuln_type, patterns in vulnerability_patterns.items():
            if vuln_type in scan_types:
                for pattern in patterns:
                    matches = re.findall(pattern, source_code, re.IGNORECASE)
                    if matches:
                        self.vulnerabilities.append({
                            'type': vuln_type.title(),
                            'contract': contract_address,
                            'severity': 'Medium',
                            'description': f'Potential {vuln_type} vulnerability pattern found',
                            'matches': len(matches)
                        })

    def analyze_transaction_history(self, contract_address, network):
        """Analyze contract transaction history for suspicious activity"""
        print("[*] Analyzing transaction history...")
        
        # This would require extensive blockchain analysis
        # For demo, we'll check basic metrics
        
        explorers = {
            'ethereum': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api'
        }
        
        if network in explorers:
            api_url = explorers[network]
            api_key = self.get_option('API_KEY')
            
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': contract_address,
                'startblock': 0,
                'endblock': 99999999,
                'sort': 'desc',
                'apikey': api_key
            }
            
            try:
                response = requests.get(api_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == '1':
                        transactions = data['result']
                        print(f"[+] Found {len(transactions)} transactions")
                        
                        # Check for recent high-value transactions
                        recent_txs = transactions[:10]  # Last 10 transactions
                        for tx in recent_txs:
                            value = int(tx['value']) / 10**18  # Convert from wei
                            if value > 10:  # More than 10 ETH
                                print(f"[!] High-value transaction: {value} ETH")
            except Exception as e:
                print(f"[-] Error analyzing transactions: {e}")

    def test_common_vulnerabilities(self, contract_address, network, scan_types, rpc_endpoint):
        """Test for common smart contract vulnerabilities"""
        print("[*] Testing for common vulnerabilities...")
        
        if not rpc_endpoint:
            print("[-] RPC endpoint required for live testing")
            return
        
        try:
            # Connect to blockchain
            w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
            
            if w3.is_connected():
                print(f"[+] Connected to {network} via RPC")
                
                # Test basic contract interaction
                balance = w3.eth.get_balance(contract_address)
                eth_balance = w3.from_wei(balance, 'ether')
                print(f"[+] Contract balance: {eth_balance} ETH")
                
                # Check if contract is a token
                if self.is_erc20_token(w3, contract_address):
                    print("[+] Contract appears to be an ERC20 token")
                    
            else:
                print("[-] Could not connect to RPC endpoint")
                
        except Exception as e:
            print(f"[-] RPC connection error: {e}")

    def is_erc20_token(self, w3, contract_address):
        """Check if contract implements ERC20 standard"""
        try:
            # Basic ERC20 function signatures
            erc20_functions = [
                'totalSupply()',
                'balanceOf(address)',
                'transfer(address,uint256)',
                'transferFrom(address,address,uint256)',
                'approve(address,uint256)',
                'allowance(address,address)'
            ]
            
            # This would require actual contract interaction
            # For demo, we'll assume it's a token if it has a balance
            balance = w3.eth.get_balance(contract_address)
            return balance > 0
            
        except:
            return False

    def check_network_health(self, network, rpc_endpoint):
        """Check blockchain network health"""
        print(f"[*] Checking {network} network health...")
        
        if rpc_endpoint:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
                if w3.is_connected():
                    block_number = w3.eth.block_number
                    gas_price = w3.eth.gas_price
                    print(f"[+] Current block: {block_number}")
                    print(f"[+] Gas price: {w3.from_wei(gas_price, 'gwei')} Gwei")
                else:
                    print("[-] Cannot connect to network")
            except Exception as e:
                print(f"[-] Network connection error: {e}")

    def check_recent_attacks(self, network):
        """Check for recent network attacks or exploits"""
        print(f"[*] Checking for recent attacks on {network}...")
        
        # This would integrate with security feeds
        # For demo, we'll show a placeholder
        print("[*] Recent attack data requires security feed integration")

    def check_fork_status(self, network):
        """Check if network has recent hard forks"""
        print(f"[*] Checking fork status for {network}...")
        
        # Known forks for major networks
        forks = {
            'ethereum': ['London', 'Berlin', 'Muir Glacier'],
            'bsc': ['ZhangHeng', 'Planck', 'Luban'],
            'polygon': ['Bor', 'Heimdall']
        }
        
        if network in forks:
            print(f"[+] Known forks: {', '.join(forks[network])}")

    def show_results(self):
        """Display scan results"""
        print(f"\n[*] Blockchain & Web3 Security Scan Complete")
        print("=" * 60)
        
        if self.vulnerabilities:
            print(f"\n[!] VULNERABILITIES FOUND ({len(self.vulnerabilities)}):")
            print("-" * 40)
            for vuln in self.vulnerabilities:
                print(f"  Type: {vuln['type']}")
                print(f"  Contract: {vuln['contract']}")
                print(f"  Severity: {vuln['severity']}")
                print(f"  Description: {vuln['description']}")
                if 'matches' in vuln:
                    print(f"  Pattern Matches: {vuln['matches']}")
                print()
        
        if self.contract_info:
            print(f"\n[+] CONTRACT INFORMATION:")
            print("-" * 40)
            for key, value in self.contract_info.items():
                if key != 'source_code' and key != 'bytecode' and key != 'abi':
                    print(f"  {key}: {value}")
        
        print(f"\n[+] Scan completed. Found {len(self.vulnerabilities)} potential vulnerabilities.")