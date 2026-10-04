#!/usr/bin/env python3
"""
Unit tests for beacon functionality
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../core'))

from beacon import ProfessionalBeacon, BeaconConfig

class TestProfessionalBeacon(unittest.TestCase):
    """Test cases for ProfessionalBeacon"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = BeaconConfig(
            checkin_interval=30,
            jitter_percent=20,
            max_retries=3
        )
        self.beacon = ProfessionalBeacon(self.config)
    
    def test_agent_id_generation(self):
        """Test secure agent ID generation"""
        agent_id = self.beacon._generate_secure_id()
        self.assertIsInstance(agent_id, str)
        self.assertEqual(len(agent_id), 32)  # 16 bytes in hex
    
    @patch('beacon.ProfessionalBeacon._safety_checks')
    @patch('beacon.ProfessionalBeacon.crypto.establish_secure_session')
    async def test_beacon_initialization(self, mock_crypto, mock_safety):
        """Test beacon initialization"""
        mock_safety.return_value = True
        mock_crypto.return_value = True
        
        result = await self.beacon.initialize()
        self.assertTrue(result)
    
    @patch('beacon.ProfessionalBeacon._safety_checks')
    async def test_safety_checks_failure(self, mock_safety):
        """Test beacon initialization failure due to safety checks"""
        mock_safety.return_value = False
        
        result = await self.beacon.initialize()
        self.assertFalse(result)
    
    def test_adaptive_sleep_calculation(self):
        """Test adaptive sleep time calculation"""
        sleep_time = self.beacon._calculate_adaptive_sleep()
        self.assertGreaterEqual(sleep_time, 10)  # Minimum 10 seconds
        
        # Test with failure backoff
        self.beacon.failed_attempts = 3
        sleep_time_with_backoff = self.beacon._calculate_adaptive_sleep()
        self.assertGreater(sleep_time_with_backoff, sleep_time)
    
    def test_advanced_jitter_calculation(self):
        """Test advanced jitter calculation"""
        jitter = self.beacon._calculate_advanced_jitter()
        
        # Should be within jitter range
        expected_min = 1 - (self.config.jitter_percent / 100)
        expected_max = 1 + (self.config.jitter_percent / 100)
        
        self.assertGreaterEqual(jitter, expected_min * 0.8)  # Account for time-based modulation
        self.assertLessEqual(jitter, expected_max * 1.3)     # Account for load-based modulation

class TestBeaconConfig(unittest.TestCase):
    """Test cases for BeaconConfig"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = BeaconConfig()
        
        self.assertEqual(config.checkin_interval, 60)
        self.assertEqual(config.jitter_percent, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertIsInstance(config.user_agents, list)
        self.assertIsInstance(config.endpoints, list)
        self.assertIsInstance(config.burn_indicators, list)
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        custom_user_agents = ['Custom Agent/1.0']
        custom_endpoints = ['/custom/endpoint']
        
        config = BeaconConfig(
            user_agents=custom_user_agents,
            endpoints=custom_endpoints,
            checkin_interval=120
        )
        
        self.assertEqual(config.user_agents, custom_user_agents)
        self.assertEqual(config.endpoints, custom_endpoints)
        self.assertEqual(config.checkin_interval, 120)

if __name__ == '__main__':
    unittest.main()