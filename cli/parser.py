#!/usr/bin/env python3
"""
CLI Parser utilities (Optional for future)
"""

import argparse

def create_advanced_parser():
    """Create advanced CLI parser for the framework"""
    parser = argparse.ArgumentParser(description='PySploit Advanced Framework')
    parser.add_argument('-m', '--module', help='Module to run directly')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    return parser
