import unittest
from unittest.mock import MagicMock, patch
from cli.console import PySploitConsole

class TestConsoleCompletion(unittest.TestCase):
    def setUp(self):
        # Create a console instance with mock framework
        self.console = PySploitConsole()
        self.console.framework = MagicMock()
        
        # Mock module manager
        self.console.module_manager = MagicMock()
        
        # Setup fake exploits and auxiliaries
        self.console.framework.exploits = {'vsftpd_234_backdoor': MagicMock(), 'smb_ms17_010': MagicMock()}
        self.console.framework.auxiliary = {'portscan': MagicMock(), 'ssh_brute': MagicMock()}

    def test_complete_use_full_match(self):
        """Test completion with partial text that matches one result"""
        results = self.console.complete_use('vsftpd', 'use vsftpd', 4, 10)
        self.assertEqual(results, ['vsftpd_234_backdoor'])
        
        results2 = self.console.complete_use('exploit/vsft', 'use exploit/vsft', 4, 16)
        self.assertEqual(results2, ['exploit/vsftpd_234_backdoor'])

    def test_complete_use_partial_multiple(self):
        """Test completion with text that matches multiple results"""
        # Let's add another exploit that starts with 's'
        self.console.framework.exploits['smb_psexec'] = MagicMock()
        
        results = self.console.complete_use('s', 'use s', 4, 5)
        self.assertIn('smb_ms17_010', results)
        self.assertIn('smb_psexec', results)
        self.assertIn('ssh_brute', results)

    def test_complete_use_empty(self):
        """Test completion with empty string"""
        results = self.console.complete_use('', 'use ', 4, 4)
        self.assertTrue(len(results) > 0)
        self.assertIn('exploit/vsftpd_234_backdoor', results)
        self.assertIn('auxiliary/portscan', results)

    def test_complete_set_no_module(self):
        """Test complete_set when no module is loaded"""
        self.console.module_manager.current_module = None
        results = self.console.complete_set('RH', 'set RH', 4, 6)
        self.assertEqual(results, [])

    def test_complete_set_with_module(self):
        """Test complete_set when module is loaded"""
        mock_module = MagicMock()
        mock_module.options = {'RHOSTS': '127.0.0.1', 'RPORT': '21', 'THREADS': '10'}
        self.console.module_manager.current_module = mock_module
        
        results = self.console.complete_set('r', 'set r', 4, 5)
        # Should return both ignoring case
        self.assertIn('RHOSTS', [r.upper() for r in results])
        self.assertIn('RPORT', [r.upper() for r in results])

    def test_complete_workspace(self):
        """Test complete_workspace from DB"""
        # Mock the DB workspace list
        self.console.framework.session_manager.db.get_workspaces.return_value = ['default', 'project_alpha', 'project_beta']
        
        results = self.console.complete_workspace('proj', 'workspace proj', 10, 14)
        self.assertEqual(results, ['project_alpha', 'project_beta'])
        
        # Test flag completion
        results = self.console.complete_workspace('proj', 'workspace -d proj', 13, 17)
        self.assertEqual(results, ['project_alpha', 'project_beta'])

    def test_complete_show(self):
        """Test complete_show command"""
        results = self.console.complete_show('opt', 'show opt', 5, 8)
        self.assertEqual(results, ['options'])
        
        results = self.console.complete_show('', 'show ', 5, 5)
        self.assertIn('payloads', results)
        self.assertIn('options', results)
        self.assertIn('info', results)

if __name__ == '__main__':
    unittest.main()
