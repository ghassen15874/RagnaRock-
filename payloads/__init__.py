#!/usr/bin/env python3
"""
Payloads Package
"""

from payloads.windows import WindowsPayloads
from payloads.linux import LinuxPayloads
from payloads.web import WebPayloads
from payloads.beacon import BeaconPayloads

__all__ = ['WindowsPayloads', 'LinuxPayloads', 'WebPayloads', 'BeaconPayloads']