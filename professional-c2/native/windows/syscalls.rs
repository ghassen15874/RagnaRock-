//! Direct syscall implementation in Rust
use winapi::um::winnt::{HANDLE, PVOID};
use std::mem;

#[repr(C)]
pub struct UNICODE_STRING {
    pub Length: u16,
    pub MaximumLength: u16,
    pub Buffer: *mut u16,
}

#[no_mangle]
pub extern "system" fn direct_nt_allocate_virtual_memory(
    process_handle: HANDLE,
    base_address: *mut PVOID,
    zero_bits: usize,
    size: *mut usize,
    allocation_type: u32,
    protect: u32,
) -> u32 {
    unsafe {
        let mut status: u32;
        
        #[cfg(target_arch = "x86_64")]
        core::arch::asm!(
            "mov r10, rcx",
            "syscall",
            in("rax") 0x18, // NtAllocateVirtualMemory
            in("rcx") process_handle,
            in("rdx") base_address,
            in("r8") zero_bits,
            in("r9") size,
            lateout("rax") status,
            lateout("rcx") _,
            lateout("rdx") _,
            lateout("r8") _,
            lateout("r9") _,
        );
        
        status
    }
}

#[no_mangle]
pub extern "system" fn direct_nt_protect_virtual_memory(
    process_handle: HANDLE,
    base_address: *mut PVOID,
    size: *mut usize,
    new_protect: u32,
    old_protect: *mut u32,
) -> u32 {
    unsafe {
        let mut status: u32;
        
        #[cfg(target_arch = "x86_64")]
        core::arch::asm!(
            "mov r10, rcx",
            "syscall",
            in("rax") 0x50, // NtProtectVirtualMemory
            in("rcx") process_handle,
            in("rdx") base_address,
            in("r8") size,
            in("r9") new_protect,
            lateout("rax") status,
            lateout("rcx") _,
            lateout("rdx") _,
            lateout("r8") _,
            lateout("r9") _,
        );
        
        status
    }
}