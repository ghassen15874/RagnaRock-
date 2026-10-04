#!/usr/bin/env python3
"""
Integration tests for full C2 stack
"""
import asyncio
import aiohttp
import unittest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestFullStackIntegration(unittest.TestCase):
    """Integration tests for full C2 stack"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_base_url = "http://localhost:8080"
        self.test_username = "test_operator"
        self.test_password = "test_password"
    
    async def asyncSetUp(self):
        """Async setup"""
        self.session = aiohttp.ClientSession()
    
    async def asyncTearDown(self):
        """Async teardown"""
        await self.session.close()
    
    async def test_api_authentication(self):
        """Test API authentication flow"""
        auth_data = {
            'username': self.test_username,
            'password': self.test_password
        }
        
        async with self.session.post(
            f"{self.api_base_url}/api/auth/login",
            json=auth_data
        ) as response:
            
            self.assertEqual(response.status, 200)
            data = await response.json()
            
            self.assertIn('access_token', data)
            self.assertIn('refresh_token', data)
            self.assertEqual(data['token_type'], 'bearer')
    
    async def test_agent_management_flow(self):
        """Test complete agent management flow"""
        # Authenticate first
        auth_data = {
            'username': self.test_username,
            'password': self.test_password
        }
        
        async with self.session.post(
            f"{self.api_base_url}/api/auth/login",
            json=auth_data
        ) as auth_response:
            
            auth_data = await auth_response.json()
            access_token = auth_data['access_token']
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Test getting agents
            async with self.session.get(
                f"{self.api_base_url}/api/agents",
                headers=headers
            ) as agents_response:
                
                self.assertEqual(agents_response.status, 200)
                agents_data = await agents_response.json()
                
                self.assertIn('agents', agents_data)
                self.assertIn('total', agents_data)
    
    async def test_task_creation_flow(self):
        """Test task creation and management flow"""
        # This would require mock agents to be present
        # For now, test the API endpoints
        pass
    
    async def test_dashboard_statistics(self):
        """Test dashboard statistics endpoint"""
        auth_data = {
            'username': self.test_username,
            'password': self.test_password
        }
        
        async with self.session.post(
            f"{self.api_base_url}/api/auth/login",
            json=auth_data
        ) as auth_response:
            
            auth_data = await auth_response.json()
            access_token = auth_data['access_token']
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            async with self.session.get(
                f"{self.api_base_url}/api/dashboard/stats",
                headers=headers
            ) as stats_response:
                
                self.assertEqual(stats_response.status, 200)
                stats_data = await stats_response.json()
                
                expected_keys = [
                    'total_agents',
                    'active_agents', 
                    'pending_tasks',
                    'platforms',
                    'recent_activity'
                ]
                
                for key in expected_keys:
                    self.assertIn(key, stats_data)

class TestBeaconIntegration(unittest.TestCase):
    """Integration tests for beacon functionality"""
    
    async def test_beacon_communication(self):
        """Test beacon communication with team server"""
        # This would require a running team server
        # Test beacon checkin, task retrieval, and result submission
        pass
    
    async def test_persistence_installation(self):
        """Test cross-platform persistence installation"""
        # Test persistence on different platforms
        # This would require platform-specific testing environments
        pass

def run_integration_tests():
    """Run all integration tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFullStackIntegration)
    suite.addTests(loader.loadTestsFromTestCase(TestBeaconIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Run integration tests
    success = run_integration_tests()
    sys.exit(0 if success else 1)