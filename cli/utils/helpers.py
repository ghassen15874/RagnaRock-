#!/usr/bin/env python3
"""
CLI Helper functions
"""

import os
import sys

def clear_screen():
    """Clear terminal screen cross-platform"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_error(msg):
    """Print standard error message"""
    print(f"[-] {msg}")

def print_success(msg):
    """Print standard success message"""
    print(f"[+] {msg}")

def print_info(msg):
    """Print standard info message"""
    print(f"[*] {msg}")
