#!/usr/bin/env python3
"""
PySploit Console - Complete Metasploit-style Interface - FIXED VERSION
"""

import cmd
import time
import sys
import os
import threading
import argparse
from core.framework import PySploitFramework
from core.payload_generator import PayloadGenerator
from core.module_manager import ModuleManager
from core.output import OutputFormatter, Fore

class PySploitConsole(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.formatter = OutputFormatter()
        self.framework = PySploitFramework()
        self.generator = PayloadGenerator(self.framework)
        self.module_manager = ModuleManager(self.framework)
        self.update_prompt()
        self.intro = self.get_banner()
    
    def update_prompt(self):
        """Update prompt based on current context"""
        workspace = self.framework.session_manager.current_workspace
        ws_prefix = f"[{self.formatter._color(workspace, Fore.CYAN)}] " if workspace != 'default' else ""
        prompt_module = self.formatter._color(self.module_manager.get_prompt(), Fore.RED)
        self.prompt = f"{ws_prefix}pysploit {prompt_module} > "
    
    def get_banner(self):
        return """
╔═╗╔═╗╔═╗╔═╗╦  ╦╔═╗╦ ╦   ╔████╗ 
╚═╗╠═╝╠═╣║  ╚╗╔╝║╣ ╚╦╝   ╚╔████╗
╚═╝╩  ╩ �╩╚═╝ ╚╝ ╚═╝ ╩     ╚╝███╔╝
                            ██╔══╝ 
                            ██████╗
                            ╚═════╝
        PySploit Framework v2.0 (Metasploit-style)
        Type 'help' or '?' for available commands
        """

    # ========== METASPLOIT-STYLE COMMANDS ==========
    
    def do_use(self, arg):
        """Select a module: use <module> or use <type>/<module>"""
        if not arg:
            print("Usage: use <module> or use <type>/<module>")
            print("Examples:")
            print("  use vsftpd_234")
            print("  use exploit/vsftpd_234") 
            print("  use auxiliary/portscan")
            print("  use auxiliary/real_cf_attack")
            return
        
        success, message = self.module_manager.use(arg)
        print(f"[*] {message}")
        if success:
            self.update_prompt()
            # Show module info and options
            print(self.module_manager.get_module_info())
            # FIX: Use show options instead of do_show_options
            self.do_show("options")
    
    def do_back(self, arg):
        """Move back from the current context"""
        message = self.module_manager.back()
        print(f"[*] {message}")
        self.update_prompt()
    
    def do_show(self, arg):
        """Show information: show [options|info|payloads|exploits|auxiliary]"""
        args = arg.split()
        
        if not args:
            print("Usage: show [options|info|payloads|exploits|auxiliary|encoders|formatters|handlers]")
            return
        
        if args[0] == "options":
            print(self.module_manager.discover_options())
        elif args[0] == "info":
            print(self.module_manager.get_module_info())
        elif args[0] == "payloads":
            self.framework.list_payloads()
        elif args[0] == "exploits":
            self.framework.list_exploits()
        elif args[0] == "auxiliary":
            self.framework.list_auxiliary()
        elif args[0] == "encoders":
            self.framework.list_encoders()
        elif args[0] == "formatters":
            self.framework.list_formatters()
        elif args[0] == "handlers":
            print("\nAvailable Handlers:")
            print("=" * 50)
            print("  tcp  - TCP reverse shell handler")
            print("  http - HTTP beacon handler")
        else:
            print("Usage: show [options|info|payloads|exploits|auxiliary|encoders|formatters|handlers]")
    
    def do_set(self, arg):
        """Set a module option: set <option> <value>"""
        if not arg:
            print("Usage: set <option> <value>")
            return
        
        args = arg.split()
        if len(args) < 2:
            print("Usage: set <option> <value>")
            return
        
        option_name = args[0]
        value = ' '.join(args[1:])
        
        success, message = self.module_manager.set_option(option_name, value)
        if success:
            print(f"[*] {message}")
        else:
            print(f"[-] {message}")
    
    def do_unset(self, arg):
        """Unset a module option: unset <option>"""
        if not arg:
            print("Usage: unset <option>")
            return
        
        success, message = self.module_manager.set_option(arg, "")
        if success:
            print(f"[*] {message}")
        else:
            print(f"[-] {message}")
    
    def do_run(self, arg):
        """Run the current module (alias for exploit)"""
        self.do_exploit(arg)
    
    def do_exploit(self, arg):
        """Run the current module"""
        if not self.module_manager.current_module:
            print("[-] No module selected. Use 'use <module>' first.")
            return
        
        print("[*] Running module...")
        success, message = self.module_manager.run()
        
        if success:
            print(f"[+] {message}")
        else:
            print(f"[-] {message}")
    
    def do_check(self, arg):
        """Check if target is vulnerable (for exploits)"""
        if not self.module_manager.current_module or self.module_manager.module_type != 'exploit':
            print("[-] No exploit module selected")
            return
        
        target = self.module_manager._get_option_value('RHOST') or self.module_manager._get_option_value('TARGET')
        if not target:
            print("[-] RHOST or TARGET not set")
            return
        
        print(f"[*] Checking target: {target}")
        try:
            if self.module_manager.current_module.check(target):
                print("[+] Target appears vulnerable")
            else:
                print("[-] Target does not appear vulnerable")
        except Exception as e:
            print(f"[-] Check failed: {e}")

    def do_search(self, arg):
        """Search for modules: search <term>"""
        if not arg:
            print("Usage: search <term>")
            return
        
        term = arg.lower()
        print(f"[*] Searching for: {term}")
        
        found = False
        
        # Search exploits
        for name, exploit in self.framework.exploits.items():
            if (term in name.lower() or 
                term in exploit.description.lower() or
                term in getattr(exploit, 'name', '').lower()):
                print(f"  exploit/{name} - {exploit.description}")
                found = True
        
        # Search auxiliary
        for name, module in self.framework.auxiliary.items():
            if (term in name.lower() or 
                term in module.description.lower() or
                term in getattr(module, 'name', '').lower()):
                print(f"  auxiliary/{name} - {module.description}")
                found = True
        
        if not found:
            print("[-] No modules found matching your search")

    # ========== ORIGINAL PAYLOAD & HANDLER COMMANDS ==========
    
    def do_generate(self, arg):
        """Generate payload: generate <payload> LHOST=<ip> LPORT=<port> [options]"""
        args = arg.split()
        if len(args) < 1:
            print("Usage: generate <payload> LHOST=<ip> LPORT=<port> [FORMAT=raw] [ENCODER=none]")
            return
        
        payload_type = args[0]
        options = {}
        
        for arg in args[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                options[key.upper()] = value
        
        try:
            lhost = options.get('LHOST')
            lport = options.get('LPORT')
            
            if not lhost or not lport:
                print("[-] LHOST and LPORT are required")
                return
            
            payload = self.generator.generate(payload_type, lhost, lport, options)
            print(f"\n[+] Generated payload:\n")
            print(payload)
            
        except Exception as e:
            print(f"[-] Error: {e}")
    
    def do_handler(self, arg):
        """Start payload handler: handler [tcp|http] LHOST=<ip> LPORT=<port>"""
        args = arg.split()
        if len(args) < 3:
            print("Usage: handler [tcp|http] LHOST=<ip> LPORT=<port>")
            print("Example: handler tcp LHOST=192.168.0.146 LPORT=4444")
            return
        
        handler_type = args[0]
        lhost = None
        lport = None
        
        # Parse options
        for arg in args[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                if key.upper() == 'LHOST':
                    lhost = value
                elif key.upper() == 'LPORT':
                    try:
                        lport = int(value)
                    except ValueError:
                        print(f"[-] Invalid LPORT: {value}")
                        return
        
        if not lhost or not lport:
            print("[-] LHOST and LPORT are required")
            return
        
        if handler_type == 'tcp':
            # Start TCP reverse shell handler
            handler_id = f"tcp_{lhost}_{lport}"
            if self.start_tcp_handler(lhost, lport, handler_id):
                self.framework.active_handlers[handler_id] = {
                    'type': 'tcp',
                    'lhost': lhost,
                    'lport': lport,
                    'thread': None
                }
                print(f"[+] TCP handler started on {lhost}:{lport}")
                print(f"[+] Handler ID: {handler_id}")
                print(f"[+] Ready to capture reverse shells")
            else:
                print(f"[-] Failed to start TCP handler on {lhost}:{lport}")
        
        elif handler_type == 'http':
            # Start HTTP beacon handler
            handler_id = f"http_{lhost}_{lport}"
            if self.start_http_handler(lhost, lport, handler_id):
                self.framework.active_handlers[handler_id] = {
                    'type': 'http',
                    'lhost': lhost,
                    'lport': lport,
                    'thread': None
                }
                print(f"[+] HTTP handler started on {lhost}:{lport}")
                print(f"[+] Handler ID: {handler_id}")
                print(f"[+] Ready to capture HTTP beacons")
            else:
                print(f"[-] Failed to start HTTP handler on {lhost}:{lport}")
        else:
            print("[-] Unknown handler type. Use 'tcp' or 'http'")

    def start_tcp_handler(self, lhost, lport, handler_id):
        """Start a TCP reverse shell handler"""
        try:
            # Start the handler in a separate thread
            handler_thread = threading.Thread(
                target=self.framework.handlers['reverse_shell'].start_tcp_handler,
                args=(lhost, lport, handler_id, self.framework.session_manager),
                daemon=True
            )
            handler_thread.start()
            
            # Store the thread reference
            self.framework.active_handlers[handler_id] = {
                'type': 'tcp',
                'lhost': lhost,
                'lport': lport,
                'thread': handler_thread
            }
            
            return True
        except Exception as e:
            print(f"[-] Failed to start TCP handler: {e}")
            return False

    def start_http_handler(self, lhost, lport, handler_id):
        """Start an HTTP beacon handler"""
        try:
            handler = self.framework.handlers.get('http')
            if not handler:
                print("[-] HTTP handler module not loaded")
                return False
                
            handler_thread = threading.Thread(
                target=handler._run_server,
                args=(lhost, lport, handler_id),
                daemon=True
            )
            handler_thread.start()
            
            # Store the thread reference
            self.framework.active_handlers[handler_id] = {
                'type': 'http',
                'lhost': lhost,
                'lport': lport,
                'thread': handler_thread
            }
            return True
        except Exception as e:
            print(f"[-] Failed to start HTTP handler: {e}")
            return False

    # ========== LEGACY EXPLOIT COMMAND ==========
    
    def do_exploit_legacy(self, arg):
        """Run exploit (legacy syntax): exploit <exploit_name> [options]"""
        args = arg.split()
        if len(args) < 1:
            print("Usage: exploit <exploit_name> [OPTION=value ...]")
            self.framework.list_exploits()
            return
        
        exploit_name = args[0]
        if exploit_name not in self.framework.exploits:
            print(f"[-] Unknown exploit: {exploit_name}")
            self.framework.list_exploits()
            return
        
        exploit = self.framework.exploits[exploit_name]
        options = {}
        
        # Parse options
        for arg in args[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                options[key.upper()] = value
                if key.upper() in exploit.options:
                    exploit.options[key.upper()]['value'] = value
                else:
                    print(f"[!] Warning: Unknown option {key.upper()} for exploit {exploit_name}")
        
        # ✅ CRITICAL FIX: Set framework reference
        if hasattr(exploit, 'set_framework'):
            exploit.set_framework(self.framework)
            print(f"[+] Framework reference set for exploit")
        else:
            print(f"[-] Exploit doesn't have set_framework method - sessions won't work")
        
        # Check required options
        missing_required = []
        for opt_name, opt_info in exploit.options.items():
            if opt_info.get('required', False) and not exploit.get_option(opt_name):
                missing_required.append(opt_name)
        
        if missing_required:
            print(f"[-] Required options not set: {', '.join(missing_required)}")
            for opt_name in missing_required:
                opt_info = exploit.options[opt_name]
                print(f"    {opt_name}: {opt_info.get('description', 'No description')}")
            return
        
        # Run the exploit
        print(f"[*] Running exploit: {exploit_name}")
        print(f"[*] Options: {options}")
        
        try:
            # Get target from RHOST or use default
            target = options.get('RHOST', 'unknown')
            
            # Run the exploit
            success = exploit.run(target, None)
            
            if success:
                print(f"[+] Exploit {exploit_name} completed successfully")
            else:
                print(f"[-] Exploit {exploit_name} failed")
                
        except Exception as e:
            print(f"[-] Error running exploit: {e}")
            import traceback
            traceback.print_exc()

    # ========== LEGACY AUXILIARY COMMAND ==========
    
    def do_auxiliary_legacy(self, arg):
        """Run auxiliary module (legacy syntax): auxiliary <module> [options]"""
        args = arg.split()
        if len(args) < 1:
            print("Usage: auxiliary <module> [OPTION=value ...]")
            self.framework.list_auxiliary()
            return
        
        module_name = args[0]
        if module_name not in self.framework.auxiliary:
            print(f"[-] Unknown auxiliary module: {module_name}")
            self.framework.list_auxiliary()
            return
        
        module = self.framework.auxiliary[module_name]
        options = {}
        
        # Parse options
        for arg in args[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                options[key.upper()] = value
                
                # Set the option in the module with type conversion
                if key.upper() in module.options:
                    option_type = module.options[key.upper()].get('type', 'string')
                    
                    # Convert value based on type
                    if option_type == 'int':
                        try:
                            value = int(value)
                        except ValueError:
                            print(f"[!] Warning: Option {key.upper()} should be integer, using as string")
                    elif option_type == 'bool':
                        value = value.lower() in ('true', 'yes', '1', 'on')
                    
                    module.options[key.upper()]['value'] = value
                else:
                    print(f"[!] Warning: Unknown option {key.upper()} for module {module_name}")
        
        # Set framework reference
        if hasattr(module, 'set_framework'):
            module.set_framework(self.framework)
        
        # Check required options
        missing_required = []
        for opt_name, opt_info in module.options.items():
            if opt_info.get('required', False) and not module.get_option(opt_name):
                missing_required.append(opt_name)
        
        if missing_required:
            print(f"[-] Required options not set: {', '.join(missing_required)}")
            for opt_name in missing_required:
                opt_info = module.options[opt_name]
                print(f"    {opt_name}: {opt_info.get('description', 'No description')}")
            return
        
        # Run the auxiliary module
        print(f"[*] Running auxiliary module: {module_name}")
        print(f"[*] Options: {options}")
        
        try:
            success = module.run()
            if success:
                print(f"[+] Auxiliary module {module_name} completed successfully")
            else:
                print(f"[-] Auxiliary module {module_name} failed")
                
        except Exception as e:
            print(f"[-] Error running auxiliary module: {e}")
            import traceback
            traceback.print_exc()

    # ========== SESSION MANAGEMENT COMMANDS ==========
    
    def do_sessions(self, arg):
        """Manage sessions: sessions [list|kill|interact|cleanup] [session_id|all]"""
        args = arg.split()
        
        if not args or args[0] == 'list':
            # List all sessions
            sessions = self.framework.session_manager.list_sessions()
            if sessions:
                rows = []
                for sid, info in sessions.items():
                    status = "ACTIVE" if info.get('active', False) else "INACTIVE"
                    socket_status = "YES" if info.get('metadata', {}).get('has_socket') else "NO"
                    rows.append([sid, info.get('type', 'unknown'), info.get('target', 'unknown'), status, socket_status])
                
                self.formatter.print_table("Active Sessions", ["Session ID", "Type", "Target", "Status", "Has Socket"], rows)
                
                # Show session statistics
                stats = self.framework.session_manager.get_session_stats()
                self.formatter.print_info(f"Statistics: Total: {stats['total']} | Active w/ socket: {stats['active_with_socket']} | Active no socket: {stats['active_no_socket']}")
            else:
                self.formatter.print_warning("No active sessions")
        
        elif args[0] == 'kill':
            if len(args) > 1:
                if args[1] == 'all':
                    # Kill all sessions
                    count = self.framework.session_manager.kill_all_sessions()
                    print(f"[+] Killed all {count} sessions")
                else:
                    # Kill specific session
                    session_id = args[1]
                    if self.framework.session_manager.close_session(session_id):
                        print(f"[+] Session {session_id} killed")
                    else:
                        print(f"[-] Session {session_id} not found")
            else:
                print("Usage: sessions kill <session_id|all>")
        
        elif args[0] == 'interact' and len(args) > 1:
            # Interact with a session
            session_id = args[1]
            self.framework.session_manager.interact_session(session_id)
        
        elif args[0] == 'cleanup':
            # Clean up dead sessions
            removed_count = self.framework.session_manager.cleanup_sessions()
            if removed_count == 0:
                print("[+] No dead sessions to clean up")
        
        elif args[0] == 'stats':
            # Show session statistics
            stats = self.framework.session_manager.get_session_stats()
            print(f"\nSession Statistics:")
            print(f"  Total sessions: {stats['total']}")
            print(f"  Active with socket: {stats['active_with_socket']}")
            print(f"  Active no socket: {stats['active_no_socket']}")
            print(f"  Inactive: {stats['inactive']}")
        
        else:
            print("Usage: sessions [list|kill <id|all>|interact <id>|cleanup|stats]")

    def do_session(self, arg):
        """Interact with a session: session <session_id>"""
        if not arg:
            print("Usage: session <session_id>")
            return
        
        session_id = arg
        self.framework.session_manager.interact_session(session_id)

    def do_shell(self, arg):
        """Execute shell command in current session: shell <command>"""
        if not arg:
            print("Usage: shell <command>")
            return
        
        # This would need to be implemented in your session manager
        print("[-] Shell command execution not yet implemented")

    # ========== PERSISTENCE COMMANDS ==========
    
    def do_persistence(self, arg):
        """Add persistence to session: persistence <session_id> <method> [options]"""
        args = arg.split()
        if len(args) < 2:
            print("Usage: persistence <session_id> <method> [OPTION=value ...]")
            print("Available methods: windows_scheduled_task, windows_registry, linux_cron, web_shell")
            return
        
        session_id = args[0]
        method = args[1]
        options = {}
        
        # Parse options
        for arg in args[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                options[key] = value
        
        # Generate payload (in real usage, this would be the actual payload)
        payload = "whoami"  # This would be the actual persistence payload
        
        if self.framework.session_manager.add_persistence(session_id, method, payload, options):
            self.formatter.print_success(f"Persistence added to session {session_id}")
        else:
            self.formatter.print_error(f"Failed to add persistence")

    # ========== DATABASE & WORKSPACE COMMANDS ==========
    
    def do_workspace(self, arg):
        """Manage workspaces: workspace [-a <name>|-d <name>|<name>]"""
        args = arg.split()
        db = self.framework.session_manager.db
        sm = self.framework.session_manager
        
        if not args:
            # List workspaces
            workspaces = db.get_workspaces()
            rows = [[("*" if ws == sm.current_workspace else ""), ws] for ws in workspaces]
            self.formatter.print_table("Workspaces", ["Active", "Name"], rows)
            return
            
        if args[0] == '-a' and len(args) > 1:
            name = args[1]
            if db.add_workspace(name):
                self.formatter.print_success(f"Added workspace: {name}")
                sm.set_workspace(name)
                self.update_prompt()
            else:
                self.formatter.print_error(f"Failed to add workspace: {name}")
            return
            
        if args[0] == '-d' and len(args) > 1:
            name = args[1]
            if name == sm.current_workspace:
                self.formatter.print_error("Cannot delete the active workspace")
                return
            if db.delete_workspace(name):
                self.formatter.print_success(f"Deleted workspace: {name}")
            else:
                self.formatter.print_error(f"Failed to delete workspace: {name}")
            return
            
        # Switch workspace
        name = args[0]
        if sm.set_workspace(name):
            self.formatter.print_info(f"Switched to workspace: {name}")
            self.update_prompt()
        else:
            self.formatter.print_error(f"Workspace not found: {name}", hint="Use 'workspace -a <name>' to create it.")

    def do_hosts(self, arg):
        """List all hosts in the database: hosts"""
        db = self.framework.session_manager.db
        sm = self.framework.session_manager
        hosts = db.get_hosts(sm.current_workspace)
        
        if not hosts:
            self.formatter.print_warning(f"No hosts found in workspace '{sm.current_workspace}'")
            return
            
        rows = []
        for host in hosts:
            host_id, ws, ip, mac, os_name, status, created, updated = host
            rows.append([host_id, ip, mac or "", os_name or "", status])
            
        self.formatter.print_table(f"Hosts in Workspace: {sm.current_workspace}", 
                                   ["ID", "IP Address", "MAC", "OS", "Status"], rows)


    def do_services(self, arg):
        """List all services for a host: services [-h|--host] <host_id>"""
        db = self.framework.session_manager.db
        
        # simple parsing
        args = arg.split()
        if not args:
            print("Usage: services <host_id>")
            return
            
        host_id = None
        for a in args:
            if a.isdigit():
                host_id = int(a)
                break
                
        if host_id is None:
            print("[-] Please provide a valid numeric host ID (see 'hosts' command)")
            return
            
        services = db.get_services(host_id)
        if not services:
            self.formatter.print_warning(f"No services found for host ID {host_id}")
            return
            
        rows = []
        for svc in services:
            svc_id, hid, port, proto, name, state, info, created, updated = svc
            rows.append([port, proto, name or "", state])
            
        self.formatter.print_table(f"Services for Host ID: {host_id}", 
                                   ["Port", "Protocol", "Service", "State"], rows)

    def do_report(self, arg):
        """Generate a report for the current workspace: report [html|markdown] [filename]"""
        from core.reporter import Reporter
        
        args = arg.split()
        format_type = args[0].lower() if args else "markdown"
        
        sm = self.framework.session_manager
        workspace = sm.current_workspace
        
        if format_type not in ["html", "markdown", "md"]:
            print("[-] Invalid format. Use 'html' or 'markdown'")
            return
            
        default_ext = "html" if format_type == "html" else "md"
        filename = args[1] if len(args) > 1 else f"report_{workspace}.{default_ext}"
        
        reporter = Reporter(sm.db)
        print(f"[*] Generating {format_type.upper()} report for workspace '{workspace}'...")
        
        if format_type == "html":
            success = reporter.generate_html(workspace, filename)
        else:
            success = reporter.generate_markdown(workspace, filename)
            
        if success:
            print(f"[+] Report successfully saved to: {filename}")
        else:
            print("[-] Failed to generate report")

    def do_db(self, arg):
        """Database management: db [save|clean|reset|stats|info]"""
        args = arg.split()
        
        if not args:
            print("Usage: db [save|clean|reset|stats|info]")
            return
        
        if args[0] == "save":
            self.framework.session_manager.save_all_sessions()
            self.formatter.print_success("All sessions saved to database")
        
        elif args[0] == "clean":
            # Clean inactive sessions from database
            if len(args) > 1 and args[1] == "force":
                removed_count = self.framework.session_manager.db.clean_database()
                print(f"[+] Database cleaned: removed {removed_count} inactive sessions")
            else:
                print("[!] This will remove all inactive sessions from database")
                print("[!] Use 'db clean force' to confirm")
        
        elif args[0] == "reset":
            # Reset entire database
            if len(args) > 1 and args[1] == "force":
                removed_count = self.framework.session_manager.db.reset_database()
                self.formatter.print_success(f"Database reset: removed {removed_count} entries")
            else:
                self.formatter.print_error("DANGEROUS: This will reset the entire database!")
                self.formatter.print_error("All sessions and persistence data will be lost!")
                self.formatter.print_error("Use 'db reset force' to confirm")
        
        elif args[0] == "stats":
            # Show database statistics
            stats = self.framework.session_manager.db.get_database_stats()
            print(f"\nDatabase Statistics:")
            print(f"  Total sessions: {stats['total_sessions']}")
            print(f"  Active sessions: {stats['active_sessions']}")
            print(f"  Inactive sessions: {stats['inactive_sessions']}")
            print(f"  Persistence entries: {stats['total_persistence']}")
            print(f"  Active persistence: {stats['active_persistence']}")
        
        elif args[0] == "info":
            sessions = self.framework.session_manager.db.load_sessions()
            print(f"\nDatabase Information:")
            print(f"  Total sessions: {len(sessions)}")
            print(f"  Active sessions: {len([s for s in sessions if s['active']])}")
            print(f"  Database file: {self.framework.session_manager.db.db_path}")
        
        else:
            print("Usage: db [save|clean|reset|stats|info]")

    # ========== IMPORT/EXPORT COMMANDS ==========
    
    def do_export(self, arg):
        """Export sessions: export [filename]"""
        filename = arg.strip() or f"sessions_export_{int(time.time())}.json"
        
        if self.framework.session_manager.export_sessions(filename):
            self.formatter.print_success(f"Sessions exported to {filename}")
        else:
            self.formatter.print_error("Export failed")

    def do_import(self, arg):
        """Import sessions: import <filename>"""
        if not arg:
            print("Usage: import <filename>")
            return
        
        if self.framework.session_manager.import_sessions(arg):
            self.formatter.print_success(f"Sessions imported from {arg}")
        else:
            self.formatter.print_error("Import failed")

    # ========== HANDLER MANAGEMENT COMMANDS ==========
    
    def do_handlers(self, arg):
        """Manage handlers: handlers [list|stop] [handler_id]"""
        args = arg.split()
        
        if not args or args[0] == 'list':
            handlers = self.framework.handlers['reverse_shell'].list_handlers()
            if handlers:
                rows = []
                for handler_id, info in handlers.items():
                    status = "LISTENING" if info.get('active') else "STOPPED"
                    rows.append([handler_id, info.get('lhost'), info.get('lport'), status])
                self.formatter.print_table("Active Handlers", ["ID", "LHOST", "LPORT", "Status"], rows)
            else:
                self.formatter.print_warning("No active handlers")
        
        elif args[0] == 'stop' and len(args) > 1:
            handler_id = args[1]
            if self.framework.handlers['reverse_shell'].stop_tcp_handler(handler_id):
                if handler_id in self.framework.active_handlers:
                    del self.framework.active_handlers[handler_id]
                print(f"[+] Handler {handler_id} stopped")
            else:
                print(f"[-] Failed to stop handler {handler_id}")
        
        else:
            print("Usage: handlers [list|stop <handler_id>]")

    # ========== SCRIPTING COMMANDS ==========
    
    def do_resource(self, arg):
        """Run commands from a resource file: resource [--verify] [--halt-on-error] <file>"""
        args = arg.split()
        if not args:
            self.formatter.print_error("Usage: resource [--verify] [--halt-on-error] <file>")
            return
            
        verify_only = '--verify' in args
        halt_on_error = '--halt-on-error' in args
        
        # Remove flags to get filename
        args = [a for a in args if not a.startswith('--')]
        if not args:
            self.formatter.print_error("Filename required")
            return
            
        filename = args[0]
        import os
        if not os.path.exists(filename):
            self.formatter.print_error(f"Resource file not found: {filename}")
            return
            
        # Security: Prevent executing administrative/system shell commands from automated files
        forbidden_commands = ['shell', 'test_session', 'debug_sessions', 'quit', 'exit']
        
        self.formatter.print_info(f"Analyzing resource script: {filename}")
        
        commands_to_run = []
        try:
            with open(filename, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    cmd_name = line.split()[0].lower()
                    if cmd_name in forbidden_commands:
                        self.formatter.print_error(f"Line {line_num}: Forbidden command '{cmd_name}' detected. Execution aborted.")
                        return
                        
                    commands_to_run.append((line_num, line))
        except Exception as e:
            self.formatter.print_error(f"Failed to read resource file: {e}")
            return
            
        if verify_only:
            self.formatter.print_success(f"Verification passed: {len(commands_to_run)} commands found, 0 forbidden.")
            return
            
        self.formatter.print_info(f"Running {len(commands_to_run)} commands from {filename}...")
        
        for line_num, cmd in commands_to_run:
            # Prevent logging secrets
            safe_cmd = cmd
            if 'password' in cmd.lower() or 'pass=' in cmd.lower() or 'secret' in cmd.lower():
                safe_cmd = "<Command contains hidden credentials>"
                
            self.formatter.print_info(f"Executing [Line {line_num}]: {safe_cmd}")
            try:
                # onecmd processes the command. If it returns True, it means quit/exit.
                stop = self.onecmd(cmd)
                if stop:
                    break
            except Exception as e:
                self.formatter.print_error(f"Error on line {line_num} ('{safe_cmd}'): {e}")
                if halt_on_error:
                    self.formatter.print_warning("Halting execution due to error.")
                    break

    # ========== DEBUG & TESTING COMMANDS ==========
    
    def do_test_session(self, arg):
        """Test if session manager works"""
        try:
            # Test creating a session manually
            session_id = self.framework.session_manager.create_session(
                "test_shell", 
                "test-target:1234"
            )
            print(f"[+] Test session created: {session_id}")
            
            # List sessions to verify
            sessions = self.framework.session_manager.list_sessions()
            print(f"[+] Sessions found: {len(sessions)}")
            for sid, info in sessions.items():
                print(f"  {sid}: {info}")
                
        except Exception as e:
            print(f"[-] Session test failed: {e}")
            import traceback
            traceback.print_exc()
    
    def do_debug_sessions(self, arg):
        """Debug session manager state"""
        try:
            print("[*] Debugging session manager...")
            
            # Check if session manager exists
            if hasattr(self.framework, 'session_manager'):
                print("[+] Session manager found")
                
                # Check sessions
                sessions = self.framework.session_manager.list_sessions()
                print(f"[+] Total sessions: {len(sessions)}")
                
                # Check session counter
                print(f"[+] Session counter: {self.framework.session_manager.session_counter}")
                
                # Check if sessions dict exists
                print(f"[+] Sessions dict type: {type(self.framework.session_manager.sessions)}")
                
            else:
                print("[-] No session manager found!")
                
        except Exception as e:
            print(f"[-] Debug error: {e}")

    # ========== EXIT COMMANDS ==========
    
    def do_exit(self, arg):
        """Exit the console"""
        print("[*] Thanks for using PySploit!")
        return True
    
    def do_quit(self, arg):
        """Exit the console"""
        return self.do_exit(arg)
    
    def do_EOF(self, arg):
        """Handle Ctrl+D exit"""
        print()
        return self.do_exit(arg)

    # ========== TAB COMPLETION ==========
    
    def complete_use(self, text, line, begidx, endidx):
        """Tab completion for use command"""
        modules = []
        
        # Add exploits
        for name in self.framework.exploits.keys():
            modules.append(f"exploit/{name}")
            modules.append(name)  # Also add short name
        
        # Add auxiliary
        for name in self.framework.auxiliary.keys():
            modules.append(f"auxiliary/{name}")
            modules.append(name)  # Also add short name
        
        if text:
            return [m for m in modules if m.startswith(text)]
        else:
            return modules
    
    def complete_set(self, text, line, begidx, endidx):
        """Tab completion for set command"""
        if not self.module_manager.current_module:
            return []
        
        options = []
        
        # Get options from module's options dict
        if hasattr(self.module_manager.current_module, 'options'):
            options = list(self.module_manager.current_module.options.keys())
        
        if text:
            return [opt for opt in options if opt.lower().startswith(text.lower())]
        else:
            return options
    
    def complete_sessions(self, text, line, begidx, endidx):
        """Tab completion for sessions command"""
        commands = ['list', 'kill', 'interact', 'cleanup', 'stats']
        if text:
            return [cmd for cmd in commands if cmd.startswith(text)]
        else:
            return commands

    def complete_workspace(self, text, line, begidx, endidx):
        """Tab completion for workspace command"""
        db = self.framework.session_manager.db
        workspaces = db.get_workspaces()
        # Handle arguments like '-a' or '-d'
        args = line.split()
        if len(args) > 1 and args[1] in ('-a', '-d'):
            if text:
                return [w for w in workspaces if w.startswith(text)]
            return workspaces
        if text:
            return [w for w in workspaces if w.startswith(text)]
        return workspaces
        
    def complete_show(self, text, line, begidx, endidx):
        """Tab completion for show command"""
        options = ['options', 'info', 'payloads', 'exploits', 'auxiliary', 'encoders', 'formatters']
        if text:
            return [opt for opt in options if opt.startswith(text)]
        return options

    # ========== HELP COMMANDS ==========
    
    def do_help(self, arg):
        """Show help for commands"""
        if arg:
            # Specific command help
            super().do_help(arg)
        else:
            # General help
            print("\nPySploit Framework Commands:")
            print("=" * 50)
            
            print("\n📦 MODULE COMMANDS:")
            print("  use <module>           - Select a module")
            print("  back                   - Go back to main context")
            print("  set <option> <value>   - Set module option")
            print("  unset <option>         - Unset module option")
            print("  show options           - Show module options")
            print("  show info              - Show module information")
            print("  run/exploit            - Run current module")
            print("  check                  - Check if target is vulnerable")
            print("  search <term>          - Search for modules")
            
            print("\n🎯 PAYLOAD COMMANDS:")
            print("  generate <payload> LHOST=... LPORT=... - Generate payload")
            print("  handler [tcp|http] LHOST=... LPORT=... - Start handler")
            print("  handlers [list|stop]                   - Manage handlers")
            
            print("\n🔧 SESSION COMMANDS:")
            print("  sessions [list|kill|interact|cleanup] - Manage sessions")
            print("  session <id>                          - Interact with session")
            print("  persistence <id> <method>             - Add persistence")
            
            print("\n💾 DATABASE & WORKSPACE COMMANDS:")
            print("  workspace [-a <name>|-d <name>|<name>] - Manage workspaces")
            print("  hosts                                 - List discovered hosts")
            print("  services <host_id>                    - List services for host")
            print("  db [save|clean|reset|stats|info]      - Database management")
            print("  export [filename]                     - Export sessions")
            print("  import <filename>                     - Import sessions")
            print("  report [html|markdown] [filename]     - Generate workspace report")
            
            print("\n🔍 INFORMATION COMMANDS:")
            print("  show payloads                         - List payloads")
            print("  show exploits                         - List exploits")
            print("  show auxiliary                        - List auxiliary modules")
            print("  show encoders                         - List encoders")
            print("  show formatters                       - List formatters")
            
            print("\n⚡ LEGACY COMMANDS:")
            print("  exploit_legacy <name> [options]       - Legacy exploit syntax")
            print("  auxiliary_legacy <name> [options]     - Legacy auxiliary syntax")
            
            print("\n❓ OTHER COMMANDS:")
            print("  resource <file>                       - Run resource script")
            print("  help [command]                        - Show help")
            print("  exit/quit                             - Exit console")
            print("  test_session                          - Test session manager")
            print("  debug_sessions                        - Debug sessions")
            
            print("\nType 'help <command>' for more information on a specific command.")

def main():
    """Main entry point for the console"""
    from core.logger import LoggerFactory
    LoggerFactory.setup()
    try:
        console = PySploitConsole()
        console.cmdloop()
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user")
    except Exception as e:
        print(f"[-] Console error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()