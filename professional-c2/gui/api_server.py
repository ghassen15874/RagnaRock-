#!/usr/bin/env python3
"""
REST API server for C2 operations
"""
from aiohttp import web
import aiohttp_cors
import json
import asyncio
import jwt
import datetime
from typing import Dict, List, Optional

class C2APIServer:
    """REST API server for C2 infrastructure"""
    
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
        self.jwt_secret = "your-secret-key-change-in-production"
        
        # Mock data storage
        self.agents = {}
        self.tasks = {}
        self.operators = {}
    
    def setup_routes(self):
        """Setup API routes"""
        self.app.router.add_post('/api/auth/login', self.handle_login)
        self.app.router.add_post('/api/auth/refresh', self.handle_refresh)
        
        self.app.router.add_get('/api/agents', self.handle_get_agents)
        self.app.router.add_get('/api/agents/{agent_id}', self.handle_get_agent)
        self.app.router.add_post('/api/agents/{agent_id}/tasks', self.handle_create_task)
        self.app.router.add_delete('/api/agents/{agent_id}', self.handle_remove_agent)
        
        self.app.router.add_get('/api/tasks', self.handle_get_tasks)
        self.app.router.add_get('/api/tasks/{task_id}', self.handle_get_task)
        
        self.app.router.add_get('/api/dashboard/stats', self.handle_dashboard_stats)
        self.app.router.get('/api/events/stream', self.handle_event_stream)
    
    def setup_cors(self):
        """Setup CORS for web interface"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
        
        # Configure CORS on all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def handle_login(self, request):
        """Handle operator authentication"""
        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')
            
            # Authentication logic (replace with real auth)
            if await self.authenticate_operator(username, password):
                token = self.generate_jwt_token(username)
                refresh_token = self.generate_refresh_token(username)
                
                return web.json_response({
                    'access_token': token,
                    'refresh_token': refresh_token,
                    'token_type': 'bearer',
                    'expires_in': 3600
                })
            else:
                return web.json_response(
                    {'error': 'Invalid credentials'}, 
                    status=401
                )
                
        except Exception as e:
            return web.json_response(
                {'error': f'Login failed: {str(e)}'}, 
                status=500
            )
    
    async def handle_refresh(self, request):
        """Handle token refresh"""
        try:
            data = await request.json()
            refresh_token = data.get('refresh_token')
            
            # Validate refresh token and issue new access token
            username = self.validate_refresh_token(refresh_token)
            if username:
                new_token = self.generate_jwt_token(username)
                return web.json_response({
                    'access_token': new_token,
                    'token_type': 'bearer',
                    'expires_in': 3600
                })
            else:
                return web.json_response(
                    {'error': 'Invalid refresh token'}, 
                    status=401
                )
                
        except Exception as e:
            return web.json_response(
                {'error': f'Token refresh failed: {str(e)}'}, 
                status=500
            )
    
    async def handle_get_agents(self, request):
        """Get list of all agents"""
        if not await self.authenticate_request(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        return web.json_response({
            'agents': list(self.agents.values()),
            'total': len(self.agents)
        })
    
    async def handle_get_agent(self, request):
        """Get specific agent details"""
        if not await self.authenticate_request(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        agent_id = request.match_info.get('agent_id')
        agent = self.agents.get(agent_id)
        
        if not agent:
            return web.json_response({'error': 'Agent not found'}, status=404)
        
        return web.json_response(agent)
    
    async def handle_create_task(self, request):
        """Create task for agent"""
        if not await self.authenticate_request(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            agent_id = request.match_info.get('agent_id')
            data = await request.json()
            
            task = {
                'task_id': self.generate_task_id(),
                'agent_id': agent_id,
                'command': data.get('command'),
                'arguments': data.get('arguments', {}),
                'created_at': datetime.datetime.utcnow().isoformat(),
                'status': 'pending',
                'operator': await self.get_operator_from_token(request)
            }
            
            self.tasks[task['task_id']] = task
            
            return web.json_response(task)
            
        except Exception as e:
            return web.json_response(
                {'error': f'Task creation failed: {str(e)}'}, 
                status=500
            )
    
    async def handle_get_tasks(self, request):
        """Get list of tasks"""
        if not await self.authenticate_request(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        return web.json_response({
            'tasks': list(self.tasks.values()),
            'total': len(self.tasks)
        })
    
    async def handle_dashboard_stats(self, request):
        """Get dashboard statistics"""
        if not await self.authenticate_request(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        stats = {
            'total_agents': len(self.agents),
            'active_agents': len([a for a in self.agents.values() if a.get('active')]),
            'pending_tasks': len([t for t in self.tasks.values() if t.get('status') == 'pending']),
            'completed_tasks': len([t for t in self.tasks.values() if t.get('status') == 'completed']),
            'platforms': self.get_platform_stats(),
            'recent_activity': self.get_recent_activity()
        }
        
        return web.json_response(stats)
    
    async def handle_event_stream(self, request):
        """Server-sent events for real-time updates"""
        if not await self.authenticate_request(request):
            return web.Response(status=401)
        
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        
        await response.prepare(request)
        
        try:
            while True:
                # Send heartbeat every 30 seconds
                await response.write(f"data: {json.dumps({'type': 'heartbeat'})}\n\n".encode())
                await asyncio.sleep(30)
                
        except Exception as e:
            print(f"Event stream error: {e}")
        finally:
            await response.write_eof()
        
        return response
    
    # Authentication and utility methods
    async def authenticate_operator(self, username: str, password: str) -> bool:
        """Authenticate operator (implement proper auth)"""
        return username == "operator" and password == "password"
    
    def generate_jwt_token(self, username: str) -> str:
        """Generate JWT token"""
        payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            'iat': datetime.datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def generate_refresh_token(self, username: str) -> str:
        """Generate refresh token"""
        payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'type': 'refresh'
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    async def authenticate_request(self, request) -> bool:
        """Authenticate API request"""
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return False
        
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return bool(payload.get('username'))
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
    
    async def get_operator_from_token(self, request) -> str:
        """Get operator username from token"""
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:]
        payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
        return payload.get('username', 'unknown')
    
    def generate_task_id(self) -> str:
        """Generate unique task ID"""
        return f"task_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(self)}"
    
    def get_platform_stats(self) -> Dict:
        """Get platform distribution statistics"""
        platforms = {}
        for agent in self.agents.values():
            platform = agent.get('platform', 'unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
        return platforms
    
    def get_recent_activity(self) -> List[Dict]:
        """Get recent activity for dashboard"""
        return [
            {
                'type': 'agent_checkin',
                'agent_id': 'agent_123',
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'message': 'Agent checked in'
            }
        ]
    
    async def start(self):
        """Start the API server"""
        print(f"🚀 Starting C2 API server on {self.host}:{self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print(f"✅ API server running on {self.host}:{self.port}")
        await asyncio.Future()

async def main():
    """Main entry point for API server"""
    server = C2APIServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())