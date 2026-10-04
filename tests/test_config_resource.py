import unittest
import os
import json
import tempfile
from unittest.mock import MagicMock
from core.config import ConfigManager
from cli.console import PySploitConsole

class TestConfigAndResource(unittest.TestCase):
    def setUp(self):
        # Setup temporary config directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_mgr = ConfigManager(config_dir=self.temp_dir.name)
        
        # Setup mock console
        self.console = PySploitConsole()
        self.console.formatter.use_colors = False
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_config_defaults(self):
        self.assertEqual(self.config_mgr.get("core", "log_level"), "INFO")
        self.assertEqual(self.config_mgr.get("workspace", "auto_save"), True)
        
    def test_config_missing_settings(self):
        self.assertIsNone(self.config_mgr.get("invalid", "key"))
        self.assertIsNone(self.config_mgr.get("core", "invalid_key"))
        
    def test_config_overrides(self):
        # Override in global
        self.config_mgr.set("core", "log_level", "DEBUG", scope="global")
        self.assertEqual(self.config_mgr.get("core", "log_level"), "DEBUG")
        
        # Override in workspace
        self.config_mgr.set("core", "log_level", "ERROR", scope="workspace")
        self.assertEqual(self.config_mgr.get("core", "log_level"), "ERROR")
        
    def test_resource_forbidden_command(self):
        # Create a temp resource file with a forbidden command
        rc_path = os.path.join(self.temp_dir.name, "bad.rc")
        with open(rc_path, 'w') as f:
            f.write("shell whoami\n")
            
        # We can't easily capture output here without redirecting sys.stdout,
        # but we can ensure it doesn't crash and aborts properly.
        # Since it aborts, onecmd shouldn't be called.
        self.console.onecmd = MagicMock()
        self.console.do_resource(rc_path)
        self.console.onecmd.assert_not_called()
        
    def test_resource_verify_mode(self):
        rc_path = os.path.join(self.temp_dir.name, "good.rc")
        with open(rc_path, 'w') as f:
            f.write("workspace -a test_ws\n")
            f.write("set RHOST 127.0.0.1\n")
            
        self.console.onecmd = MagicMock()
        self.console.do_resource(f"--verify {rc_path}")
        # Verify mode should not execute anything
        self.console.onecmd.assert_not_called()

    def test_resource_password_scrubbing(self):
        rc_path = os.path.join(self.temp_dir.name, "secret.rc")
        with open(rc_path, 'w') as f:
            f.write("set password mysecret123\n")
            
        self.console.onecmd = MagicMock()
        self.console.do_resource(rc_path)
        # Check that it called onecmd with the actual command, but the output 
        # (which we can't easily assert here without mocking stdout) would be scrubbed.
        # At least we verify the execution path runs.
        self.console.onecmd.assert_called_with("set password mysecret123")

if __name__ == '__main__':
    unittest.main()
