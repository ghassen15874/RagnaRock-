import os
import json

class ConfigManager:
    """Manages configuration for RagnaRok Framework with layered priorities:
       Defaults -> Global (User) -> Workspace
    """
    def __init__(self, config_dir="~/.ragnarok"):
        self.config_dir = os.path.expanduser(config_dir)
        self.global_config_path = os.path.join(self.config_dir, "config.json")
        self.workspace_configs_dir = os.path.join(self.config_dir, "workspaces")
        self.defaults = {
            "core": {
                "log_level": "INFO",
                "color_output": True,
                "api_port": 5000,
                "api_host": "127.0.0.1"
            },
            "workspace": {
                "auto_save": True,
                "default_threads": 10,
                "timeout": 5.0
            }
        }
        self.global_config = {}
        self.workspace_config = {}
        self.current_workspace = "default"
        
        self._init_dirs()
        self.load_configs()

    def _init_dirs(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if not os.path.exists(self.workspace_configs_dir):
            os.makedirs(self.workspace_configs_dir)
            
        if not os.path.exists(self.global_config_path):
            with open(self.global_config_path, 'w') as f:
                json.dump(self.defaults, f, indent=4)

    def load_configs(self):
        """Load global config and merge with defaults"""
        try:
            if os.path.exists(self.global_config_path):
                with open(self.global_config_path, 'r') as f:
                    self.global_config = json.load(f)
            else:
                self.global_config = {}
        except Exception as e:
            print(f"[-] Failed to load global config: {e}")
            self.global_config = {}

    def set_workspace(self, workspace_name):
        """Switch workspace configuration context"""
        self.current_workspace = workspace_name
        ws_config_path = os.path.join(self.workspace_configs_dir, f"{workspace_name}.json")
        try:
            if os.path.exists(ws_config_path):
                with open(ws_config_path, 'r') as f:
                    self.workspace_config = json.load(f)
            else:
                self.workspace_config = {}
        except Exception as e:
            print(f"[-] Failed to load workspace config for {workspace_name}: {e}")
            self.workspace_config = {}

    def get(self, section, key):
        """Get a configuration value, resolving priorities: Workspace -> Global -> Default"""
        if section in self.workspace_config and key in self.workspace_config[section]:
            return self.workspace_config[section][key]
            
        if section in self.global_config and key in self.global_config[section]:
            return self.global_config[section][key]
            
        if section in self.defaults and key in self.defaults[section]:
            return self.defaults[section][key]
            
        return None

    def set(self, section, key, value, scope="global"):
        """Set a configuration value in the given scope and save it"""
        if scope == "workspace":
            if section not in self.workspace_config:
                self.workspace_config[section] = {}
            self.workspace_config[section][key] = value
            self.save_workspace_config()
        else:
            if section not in self.global_config:
                self.global_config[section] = {}
            self.global_config[section][key] = value
            self.save_global_config()

    def save_global_config(self):
        with open(self.global_config_path, 'w') as f:
            json.dump(self.global_config, f, indent=4)
            
    def save_workspace_config(self):
        ws_config_path = os.path.join(self.workspace_configs_dir, f"{self.current_workspace}.json")
        with open(ws_config_path, 'w') as f:
            json.dump(self.workspace_config, f, indent=4)
