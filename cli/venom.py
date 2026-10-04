#!/usr/bin/env python3
"""
MSFVenom-like CLI
"""

import argparse
import sys
from core.framework import PySploitFramework
from core.payload_generator import PayloadGenerator

class PySploitVenom:
    def __init__(self, quiet=False):
        self.framework = PySploitFramework(quiet=quiet)
        self.generator = PayloadGenerator(self.framework)
    
    def setup_parser(self):
        parser = argparse.ArgumentParser(description='PySploit-Venom - Payload Generator')
        
        parser.add_argument('-p', '--payload', required=True, help='Payload type')
        parser.add_argument('--lhost', required=True, help='Listener host')
        parser.add_argument('--lport', required=True, type=int, help='Listener port')
        parser.add_argument('-f', '--format', default='raw', help='Output format')
        parser.add_argument('-e', '--encoder', help='Encoder to use')
        parser.add_argument('-o', '--output', help='Output file')
        parser.add_argument('--list-payloads', action='store_true', help='List payloads')
        parser.add_argument('--list-encoders', action='store_true', help='List encoders')
        
        return parser
    
    def run(self):
        parser = self.setup_parser()
        args = parser.parse_args()
        
        if args.list_payloads:
            self.framework.list_payloads()
            return
        
        if args.list_encoders:
            self.framework.list_encoders()
            return
        
        options = {}
        if args.format:
            options['format'] = args.format
        if args.encoder:
            options['encoder'] = args.encoder
        
        try:
            payload = self.generator.generate(
                args.payload,
                args.lhost,
                args.lport,
                options
            )
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(payload)
                print(f"[+] Payload saved to: {args.output}")
            else:
                print(payload)
                
        except Exception as e:
            print(f"[-] Error: {e}")
            sys.exit(1)

def main():
    venom = PySploitVenom()
    venom.run()

if __name__ == "__main__":
    main()