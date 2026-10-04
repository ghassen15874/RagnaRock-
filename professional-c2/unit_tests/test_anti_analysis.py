#!/usr/bin/env python3
"""
Evasion technique testing
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../core'))

from evasion import AntiAnalysis, TrafficMorphing

class TestAntiAnalysis(unittest.TestCase):
    """Test cases for anti-analysis techniques"""
    
    def setUp(self):
        self.anti_analysis = AntiAnalysis()
    
    @patch('evasion.psutil.process_iter')
    def test_analysis_tools_detection(self, mock_process_iter):
        """Test detection of analysis tools"""
        # Mock processes including analysis tools
        mock_processes = [
            MagicMock(info={'name': 'python.exe'}),
            MagicMock(info={'name': 'ollydbg.exe'}),
            MagicMock(info={'name': 'wireshark.exe'})
        ]
        mock_process_iter.return_value = mock_processes
        
        result = self.anti_analysis.check_analysis_tools()
        self.assertTrue(result)
    
    @patch('evasion.psutil.process_iter')
    def test_no_analysis_tools_detected(self, mock_process_iter):
        """Test when no analysis tools are present"""
        # Mock normal processes
        mock_processes = [
            MagicMock(info={'name': 'python.exe'}),
            MagicMock(info={'name': 'notepad.exe'}),
            MagicMock(info={'name': 'chrome.exe'})
        ]
        mock_process_iter.return_value = mock_processes
        
        result = self.anti_analysis.check_analysis_tools()
        self.assertFalse(result)
    
    @patch('evasion.psutil.virtual_memory')
    @patch('evasion.psutil.cpu_count')
    def test_sandbox_resource_detection(self, mock_cpu_count, mock_virtual_memory):
        """Test sandbox resource detection"""
        # Mock limited resources (sandbox-like)
        mock_cpu_count.return_value = 1
        mock_virtual_memory.return_value = MagicMock(total=1 * 1024**3)  # 1GB
        
        result = self.anti_analysis._check_system_resources()
        self.assertTrue(result)
    
    @patch('evasion.psutil.virtual_memory')
    @patch('evasion.psutil.cpu_count')
    def test_normal_resource_detection(self, mock_cpu_count, mock_virtual_memory):
        """Test normal resource detection"""
        # Mock normal resources
        mock_cpu_count.return_value = 8
        mock_virtual_memory.return_value = MagicMock(total=16 * 1024**3)  # 16GB
        
        result = self.anti_analysis._check_system_resources()
        self.assertFalse(result)
    
    @patch('os.path.exists')
    def test_sandbox_artifacts_detection(self, mock_exists):
        """Test sandbox artifacts detection"""
        # Mock sandbox artifact paths
        mock_exists.side_effect = lambda path: 'sandbox' in path or 'analysis' in path
        
        result = self.anti_analysis._check_sandbox_artifacts()
        self.assertTrue(result)

class TestTrafficMorphing(unittest.TestCase):
    """Test cases for traffic morphing"""
    
    def setUp(self):
        self.traffic_morphing = TrafficMorphing()
    
    async def test_traffic_profile_initialization(self):
        """Test traffic profile initialization"""
        await self.traffic_morphing.initialize('google_analytics')
        self.assertIsNotNone(self.traffic_morphing.current_profile)
        self.assertEqual(
            self.traffic_morphing.current_profile['user_agent'],
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
    
    async def test_request_morphing(self):
        """Test request morphing with different profiles"""
        test_data = b"test_beacon_data"
        
        profiles = ['google_analytics', 'azure_monitor', 'aws_cloudwatch']
        
        for profile in profiles:
            await self.traffic_morphing.initialize(profile)
            morphed_request = await self.traffic_morphing.morph_request(test_data, profile)
            
            self.assertIn('method', morphed_request)
            self.assertIn('url', morphed_request)
            self.assertIn('headers', morphed_request)
            self.assertIn('body', morphed_request)
            
            # Verify profile-specific characteristics
            if profile == 'google_analytics':
                self.assertIn('google-analytics.com', morphed_request['url'])
            elif profile == 'azure_monitor':
                self.assertEqual(morphed_request['headers']['Content-Type'], 'application/json')

class TestEvasionEffectiveness(unittest.TestCase):
    """Test evasion technique effectiveness"""
    
    def test_multiple_evasion_techniques(self):
        """Test combination of evasion techniques"""
        anti_analysis = AntiAnalysis()
        
        # Test that multiple techniques work together
        # This would require more sophisticated testing environment
        pass
    
    async def test_end_to_end_evasion(self):
        """Test end-to-end evasion workflow"""
        # Test complete evasion workflow from beacon initialization to communication
        # This would require integration with actual analysis environments
        pass

def run_evasion_tests():
    """Run all evasion tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAntiAnalysis)
    suite.addTests(loader.loadTestsFromTestCase(TestTrafficMorphing))
    suite.addTests(loader.loadTestsFromTestCase(TestEvasionEffectiveness))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Run evasion tests
    success = run_evasion_tests()
    sys.exit(0 if success else 1)