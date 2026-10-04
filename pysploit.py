#!/usr/bin/env python3
"""
PySploit Framework - Main Launcher
Advanced Penetration Testing Framework
"""

import sys
import os

# Add the core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cli'))

def show_banner():
    from cli.utils.constants import BANNER
    print(BANNER)

def main():
    # Only show banner if not running in venom mode (which should output payload only)
    if len(sys.argv) > 1 and sys.argv[1] == 'venom':
        pass
    else:
        show_banner()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'venom':
        # MSFVenom mode
        from cli.venom import PySploitVenom
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        venom = PySploitVenom(quiet=True)
        venom.run()
    else:
        # MSFConsole mode (default)
        from cli.console import PySploitConsole
        console = PySploitConsole()
        console.cmdloop()

if __name__ == "__main__":
    main()