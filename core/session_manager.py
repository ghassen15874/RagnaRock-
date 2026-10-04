#!/usr/bin/env python3
"""
Session Management System
"""

import threading
import time
import json
import socket
import subprocess
from datetime import datetime
from core.session_db import SessionDatabase
from core.persistence import PersistenceManager

class Session:
    def __init__(self, session_id, session_type, target_info, workspace='default'):
        self.session_id = session_id
        self.session_type = session_type
        self.target_info = target_info
        self.workspace = workspace
        self.created_at = datetime.now()
        self.last_seen = datetime.now()
        self.active = True
        self.process = None
        self.socket = None
        self.metadata = {}
        
    def update_last_seen(self):
        self.last_seen = datetime.now()
    
    def close(self):
        self.active = False
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'type': self.session_type,
            'target': self.target_info,
            'workspace': self.workspace,
            'created_at': self.created_at.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'active': self.active,
            'metadata': self.metadata
        }

class SessionManager:
    def __init__(self, quiet=False):
        self.sessions = {}
        self.session_counter = 0
        self.lock = threading.Lock()
        self.db = SessionDatabase()
        self.persistence = PersistenceManager(self.db)
        self.quiet = quiet
        self.current_workspace = 'default'

        # Load existing sessions from database
        self.load_persisted_sessions()

    def set_workspace(self, workspace):
        if workspace not in self.db.get_workspaces():
            return False
        self.current_workspace = workspace
        return True

    def load_persisted_sessions(self):
        """Load sessions from database on startup.

        Loaded sessions are marked inactive because we cannot verify
        whether their sockets/processes are still alive after a restart.
        The session_counter is seeded from the highest persisted counter
        value so that new session IDs never collide with existing ones.
        """
        try:
            saved_sessions = self.db.load_sessions()
            max_counter = 0
            for session_data in saved_sessions:
                session = Session(
                    session_data['session_id'],
                    session_data['type'],
                    session_data['target'],
                    session_data.get('workspace', 'default')
                )
                session.created_at = datetime.fromisoformat(session_data['created_at'])
                session.last_seen = datetime.fromisoformat(session_data['last_seen'])
                # Sessions restored from DB cannot have live sockets; mark inactive.
                session.active = False
                session.metadata = session_data.get('metadata', {})

                self.sessions[session_data['session_id']] = session

                # Track highest counter to avoid ID collisions on next create.
                try:
                    parts = session_data['session_id'].rsplit('-', 1)
                    if len(parts) == 2:
                        counter_val = int(parts[1])
                        if counter_val > max_counter:
                            max_counter = counter_val
                except (ValueError, IndexError):
                    pass

            self.session_counter = max_counter
            if not self.quiet:
                print(f"[+] Loaded {len(saved_sessions)} sessions from database (counter seeded at {max_counter})")
        except Exception as e:
            if not self.quiet:
                print(f"[-] Failed to load sessions: {e}")
    
    # NOTE: create_session is defined once below (line ~424). The old
    # duplicate at this location has been removed to fix bug B1.
    def save_all_sessions(self):
        """Save all sessions to database"""
        with self.lock:
            for session in self.sessions.values():
                self.db.save_session(session)
            print("[+] All sessions saved to database")
            
    def export_sessions(self, filename):
        """Export sessions to file"""
        return self.db.export_sessions(filename, self.current_workspace)
    
    def import_sessions(self, filename):
        """Import sessions from file"""
        return self.db.import_sessions(filename)
    
    def add_persistence(self, session_id, method, payload, options=None):
        """Add persistence to session"""
        if session_id not in self.sessions:
            print(f"[-] Session {session_id} not found")
            return False
        
        return self.persistence.add_persistence(session_id, method, payload, options)
    
    def get_persistence_methods(self, session_id):
        """Get persistence methods for session"""
        return self.db.get_persistence_methods(session_id)
    
    def get_session(self, session_id):
        session = self.sessions.get(session_id)
        if session and session.workspace == self.current_workspace:
            return session
        return None
    
    def list_sessions(self):
        return {sid: session.to_dict() for sid, session in self.sessions.items() if session.workspace == self.current_workspace}
    
    def close_session(self, session_id):
        """Close a specific session"""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].close()
                del self.sessions[session_id]
                
                # Also update database
                self.db.deactivate_session(session_id)
                
                print(f"[+] Session {session_id} closed")
                return True
            return False
    def kill_all_sessions(self):
        """Kill all active sessions"""
        with self.lock:
            session_count = len(self.sessions)
            for session_id in list(self.sessions.keys()):
                self.sessions[session_id].close()
                del self.sessions[session_id]
            
            # Deactivate all sessions in database
            self.db.deactivate_all_sessions()
            
            print(f"[+] Killed all {session_count} sessions")
            return session_count

    def cleanup_sessions(self):
        """Clean up inactive/dead sessions from memory and database (fixes B10)."""
        with self.lock:
            removed_count = 0
            dead_sessions = []

            for session_id, session in list(self.sessions.items()):
                if not session.active:
                    dead_sessions.append(session_id)
                elif session.socket:
                    try:
                        session.socket.getpeername()
                    except OSError:
                        dead_sessions.append(session_id)

            for session_id in dead_sessions:
                self.sessions[session_id].close()
                del self.sessions[session_id]
                # Keep DB in sync — fixes B10
                try:
                    self.db.deactivate_session(session_id)
                except Exception as db_err:
                    print(f"[-] Failed to deactivate session {session_id} in DB: {db_err}")
                removed_count += 1

            if removed_count > 0:
                print(f"[+] Cleaned up {removed_count} dead sessions")
            else:
                print("[+] No dead sessions found")

            return removed_count

    def get_session_stats(self):
        """Get session statistics"""
        with self.lock:
            total = len(self.sessions)
            active_with_socket = 0
            active_no_socket = 0
            inactive = 0
            
            for session in self.sessions.values():
                if session.active:
                    if session.socket:
                        active_with_socket += 1
                    else:
                        active_no_socket += 1
                else:
                    inactive += 1
            
            return {
                'total': total,
                'active_with_socket': active_with_socket,
                'active_no_socket': active_no_socket,
                'inactive': inactive
            }
    
    def interact_session(self, session_id):
        session = self.get_session(session_id)
        if not session:
            print(f"[-] Session {session_id} not found")
            return False
        
        print(f"[*] Interacting with session {session_id}")
        print(f"[*] Type: {session.session_type}")
        print(f"[*] Target: {session.target_info}")
        
        if session.session_type == "reverse_shell":
            return self.interact_reverse_shell(session)
        elif session.session_type == "meterpreter":
            return self.interact_meterpreter(session)
        elif session.session_type == "test_shell":
            return self.interact_test_shell(session)
        elif session.session_type == "beacon":
            return self.interact_beacon(session)
        else:
            print(f"[-] Unknown session type: {session.session_type}")
            return False
    
    def interact_reverse_shell(self, session):
        """Interact with reverse shell session that has an active socket"""
        try:
            if not session.socket:
                print("[-] No active socket connection in this session")
                print("[*] This session was created but no reverse shell connected")
                print("[*] Make sure your handler is running and the exploit sent the payload")
                return False
            
            print(f"[*] Reverse Shell Session: {session.session_id}")
            print(f"[*] Target: {session.target_info}")
            print(f"[*] Type commands to execute on the target")
            print(f"[*] Type 'exit' to return to main console")
            print(f"[*] Type 'background' to leave session active")
            
            session.socket.settimeout(0.5)  # Non-blocking for better interaction
            
            while session.active:
                try:
                    # Get command from user
                    command = input("shell> ").strip()
                    
                    if command.lower() == 'exit':
                        print("[*] Closing session and connection...")
                        session.close()
                        break
                    elif command.lower() == 'background':
                        print("[*] Backgrounding session (connection remains active)")
                        break
                    elif command == '':
                        continue
                    else:
                        # Send command to target
                        session.socket.send((command + '\n').encode())
                        
                        # Receive response
                        time.sleep(0.5)  # Wait for command execution
                        response = self.receive_socket_data(session.socket)
                        if response:
                            print(response.decode('utf-8', errors='ignore'))
                        else:
                            print("[*] No response received")
                            
                except socket.timeout:
                    # Expected for non-blocking sockets
                    continue
                except BrokenPipeError:
                    print("[-] Connection lost - target disconnected")
                    session.active = False
                    break
                except ConnectionResetError:
                    print("[-] Connection reset by target")
                    session.active = False
                    break
                except KeyboardInterrupt:
                    print("\n[*] Backgrounding session (Ctrl+C again to exit)")
                    break
                except Exception as e:
                    print(f"[-] Error: {e}")
                    break
                    
        except Exception as e:
            print(f"[-] Interaction error: {e}")

    def receive_socket_data(self, sock, timeout=1):
        """Receive all available data from socket"""
        try:
            sock.settimeout(timeout)
            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            return data
        except socket.timeout:
            return data  # Return whatever we've received so far
        except:
            return data

    def show_reverse_shell_help(self, session):
        """Show help for reverse shell session"""
        print("""
    Available commands:
    help      - Show this help message
    info      - Show detailed session information
    status    - Check session status
    listener  - Show listener connection details
    exploit   - Show exploit information
    exit      - Leave this session

    Shell Access:
    The actual shell interaction happens through your listener.
    Use the 'listener' command to see connection details.
        """)

    def show_listener_info(self, session):
        """Show listener connection information"""
        if session.metadata and 'LHOST' in session.metadata:
            lhost = session.metadata.get('LHOST')
            lport = session.metadata.get('LPORT')
            print(f"\n[*] Listener Configuration:")
            print(f"    Host: {lhost}")
            print(f"    Port: {lport}")
            print(f"    Command: nc -lvnp {lport}")
            print(f"    OR: ncat -lvnp {lport}")
            print(f"    OR: socat - TCP-LISTEN:{lport},reuseaddr,fork")
            print(f"\n[*] Start your listener in a separate terminal:")
            print(f"    $ nc -lvnp {lport}")
            print(f"\n[*] The reverse shell should connect automatically")
        else:
            print("[-] No listener information available in session metadata")

    def show_exploit_info(self, session):
        """Show exploit information"""
        if session.metadata:
            print(f"\n[*] Exploit Information:")
            print(f"    Type: {session.metadata.get('exploit', 'unknown')}")
            print(f"    Target: {session.metadata.get('RHOST', 'unknown')}:{session.metadata.get('RPORT', 'unknown')}")
            print(f"    Payload: {session.metadata.get('payload_type', 'unknown')}")
            print(f"    Backdoor Port: {session.metadata.get('backdoor_port', 'unknown')}")
        else:
            print("[-] No exploit information available")

    def show_reverse_shell_info(self, session):
        """Show reverse shell connection information"""
        print(f"\n[*] Reverse Shell Information:")
        print(f"    Session ID: {session.session_id}")
        print(f"    Target: {session.target_info}")
        print(f"    Created: {session.created_at}")
        print(f"    Status: {'ACTIVE' if session.active else 'INACTIVE'}")
        
        # Extract LHOST and LPORT from target info if possible
        if "LHOST" in session.metadata:
            lhost = session.metadata.get("LHOST")
            lport = session.metadata.get("LPORT", "unknown")
            print(f"    Listener: {lhost}:{lport}")
            print(f"    Start listener with: nc -lvnp {lport}")
        else:
            print("    Listener: Check your exploit options for LHOST/LPORT")
        
        print(f"    Note: The reverse shell connects TO your machine")
        print(f"    Make sure your listener is running on the specified port\n")
    
    def create_shell_session(self, target_info, shell_connection):
        """Create a session from a shell connection"""
        session_id = self.create_session("reverse_shell", target_info)
        session = self.get_session(session_id)
        session.socket = shell_connection
        return session_id
    
    def interact_meterpreter(self, session):
        """Interact with meterpreter-like session"""
        print("[*] Meterpreter session - basic commands available")
        print("Available commands: help, sysinfo, shell, download, upload, exit")
        
        while session.active:
            try:
                cmd = input("meterpreter> ")
                if cmd == 'exit':
                    break
                elif cmd == 'help':
                    print("""
help      - Show this help
sysinfo   - Get system information  
shell     - Spawn system shell
download  - Download file (usage: download <remote> <local>)
upload    - Upload file (usage: upload <local> <remote>)
exit      - Exit session
                    """)
                elif cmd == 'sysinfo':
                    print("[*] Gathering system information...")
                    # Simulate system info
                    info = {
                        'OS': 'Windows 10',
                        'Architecture': 'x64',
                        'User': 'SYSTEM',
                        'Hostname': 'TARGET-PC'
                    }
                    for k, v in info.items():
                        print(f"    {k}: {v}")
                elif cmd == 'shell':
                    print("[*] Spawning system shell...")
                    self.interact_reverse_shell(session)
                elif cmd.startswith('download'):
                    print("[*] Download functionality - coming soon")
                elif cmd.startswith('upload'):
                    print("[*] Upload functionality - coming soon")
                else:
                    print(f"[-] Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                break
    def create_session(self, session_type, target_info):
        """Create a new session (canonical definition — B1 duplicate removed)."""
        with self.lock:
            self.session_counter += 1
            session_id = f"{session_type}-{self.session_counter}"
            session = Session(session_id, session_type, target_info, self.current_workspace)
            self.sessions[session_id] = session

            try:
                self.db.save_session(session)
            except Exception as e:
                print(f"[-] Failed to save session to database: {e} (session still active in memory)")

            print(f"[+] Session {session_id} created")
            return session_id
    def interact_test_shell(self, session):
        """Interact with test shell session"""
        print("[*] Test shell session - this is a simulated session for testing")
        print("[*] Type 'exit' to return to main console")
        
        while session.active:
            try:
                command = input("test_shell> ")
                if command.lower() == 'exit':
                    break
                elif command.lower() == 'help':
                    print("""
    Available commands:
    help     - Show this help
    whoami   - Simulate user info
    pwd      - Simulate current directory  
    ls       - Simulate file listing
    id       - Simulate user ID
    exit     - Exit session
                    """)
                elif command.lower() == 'whoami':
                    print("root")
                elif command.lower() == 'pwd':
                    print("/root")
                elif command.lower() == 'ls':
                    print("bin  etc  home  lib  root  usr  var")
                elif command.lower() == 'id':
                    print("uid=0(root) gid=0(root) groups=0(root)")
                else:
                    print(f"test_shell: command not found: {command}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[-] Error: {e}")
                break
        
        return True

    def interact_beacon(self, session):
        """Interact with HTTP beacon session"""
        import uuid
        
        print("[*] HTTP Beacon Session - Commands are queued until beacon checks in")
        print("[*] Available commands: exit, background, info, <shell_command>")
        
        # Ensure session has tasks and results attributes
        if not hasattr(session, 'tasks'):
            session.tasks = []
        if not hasattr(session, 'results'):
            session.results = {}
            
        while session.active:
            try:
                cmd = input("beacon> ").strip()
                
                if cmd.lower() in ('exit', 'background'):
                    print("[*] Backgrounding beacon session")
                    break
                elif cmd.lower() == 'info':
                    print("\nBeacon Information:")
                    for k, v in session.metadata.items():
                        print(f"  {k}: {v}")
                    print(f"  Last check-in: {datetime.fromtimestamp(session.last_seen).strftime('%Y-%m-%d %H:%M:%S') if hasattr(session, 'last_seen') and isinstance(session.last_seen, float) else session.last_seen}")
                    print(f"  Pending tasks: {len(session.tasks)}")
                    print()
                elif cmd:
                    # Queue the command as a task
                    task_id = str(uuid.uuid4())
                    task = {
                        'task_id': task_id,
                        'type': 'shell',
                        'command': cmd
                    }
                    session.tasks.append(task)
                    print(f"[*] Task {task_id} queued. Waiting for beacon check-in...")
                    
                    # Wait for result
                    wait_count = 0
                    max_waits = 30  # Wait up to 30 seconds
                    found_result = False
                    
                    while wait_count < max_waits:
                        if task_id in session.results:
                            result = session.results.pop(task_id)
                            output = result.get('output', '')
                            if output:
                                print(f"\n[+] Task output:\n{output}")
                            else:
                                print(f"\n[+] Task completed with no output")
                            found_result = True
                            break
                        
                        time.sleep(1)
                        wait_count += 1
                        
                    if not found_result:
                        print(f"[-] Task timed out waiting for beacon check-in (task remains queued)")
                        
            except KeyboardInterrupt:
                print("\n[*] Backgrounding beacon session")
                break
            except Exception as e:
                print(f"[-] Error interacting with beacon: {e}")
                break
                
        return True