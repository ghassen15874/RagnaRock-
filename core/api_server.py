import threading
from flask import Flask, request, jsonify, abort
import json
import secrets

class RestAPI:
    def __init__(self, framework, host='127.0.0.1', port=5000):
        self.framework = framework
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.api_token = secrets.token_hex(32)
        self.setup_routes()

    def setup_routes(self):
        @self.app.before_request
        def verify_token():
            token = request.headers.get('X-Api-Token')
            if not token or token != self.api_token:
                abort(401, description="Unauthorized: Invalid API token")

        @self.app.route('/api/v1/sessions', methods=['GET'])
        def get_sessions():
            sessions = self.framework.session_manager.list_sessions()
            return jsonify({'sessions': sessions})

        @self.app.route('/api/v1/workspaces', methods=['GET'])
        def get_workspaces():
            workspaces = self.framework.session_manager.db.get_workspaces()
            return jsonify({'workspaces': workspaces})
            
        @self.app.route('/api/v1/workspaces', methods=['POST'])
        def create_workspace():
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({'error': 'name required'}), 400
                
            name = data['name']
            desc = data.get('description', '')
            if self.framework.session_manager.db.add_workspace(name, desc):
                return jsonify({'status': 'success', 'workspace': name}), 201
            return jsonify({'error': 'failed to create workspace'}), 400

        @self.app.route('/api/v1/hosts', methods=['GET'])
        def get_hosts():
            workspace = request.args.get('workspace', self.framework.session_manager.current_workspace)
            hosts = self.framework.session_manager.db.get_hosts(workspace)
            host_list = [
                {'id': h[0], 'workspace': h[1], 'ip': h[2], 'mac': h[3], 'os': h[4], 'status': h[5]} 
                for h in hosts
            ]
            return jsonify({'hosts': host_list})

        @self.app.route('/api/v1/modules/run', methods=['POST'])
        def run_module():
            data = request.get_json()
            if not data or 'module' not in data:
                return jsonify({'error': 'module name required'}), 400
                
            module_name = data['module']
            options = data.get('options', {})
            
            # This is a simplified async execution wrapper for the API
            # In a real framework, you'd have a task queue for this
            def run_task():
                module = None
                if module_name in self.framework.exploits:
                    module = self.framework.exploits[module_name](self.framework)
                elif module_name in self.framework.auxiliary:
                    module = self.framework.auxiliary[module_name](self.framework)
                    
                if module:
                    for k, v in options.items():
                        module.set_option(k, v)
                    try:
                        module.run()
                    except Exception as e:
                        print(f"[-] API Module Error: {e}")
            
            thread = threading.Thread(target=run_task)
            thread.daemon = True
            thread.start()
            
            return jsonify({'status': 'started', 'module': module_name})

    def run(self):
        print(f"\n[+] Starting RagnaRok REST API on {self.host}:{self.port}")
        print(f"[!] API Token: {self.api_token}")
        print("[!] Keep this token secret. Use header: X-Api-Token")
        
        # Disable Flask default logging
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

    def start_background(self):
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        return self.api_token
