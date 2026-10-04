#!/usr/bin/env python3
"""
CI/CD build system for cross-platform deployment
"""
import os
import sys
import subprocess
import platform
from pathlib import Path
import json

class CICDBuilder:
    """CI/CD build system for professional C2"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        
    def build_all(self) -> bool:
        """Build all components for all platforms"""
        print("🏗️  Building professional C2 framework...")
        
        # Clean previous builds
        self._clean_build()
        
        # Build native components for current platform
        if not self._build_native_components():
            return False
        
        # Package Python components
        if not self._package_python():
            return False
        
        # Generate deployment manifests
        self._generate_manifests()
        
        print("✅ Build completed successfully")
        return True
    
    def _build_native_components(self) -> bool:
        """Build platform-specific native components"""
        current_platform = platform.system().lower()
        native_dir = self.project_root / "native" / current_platform
        
        if not native_dir.exists():
            print(f"⚠️  No native components for {current_platform}")
            return True
        
        print(f"🔨 Building native components for {current_platform}...")
        
        try:
            if current_platform == "windows":
                return self._build_windows_native(native_dir)
            elif current_platform == "linux":
                return self._build_linux_native(native_dir)
            elif current_platform == "darwin":
                return self._build_macos_native(native_dir)
            else:
                print(f"❌ Unsupported platform: {current_platform}")
                return False
                
        except Exception as e:
            print(f"❌ Native build failed: {e}")
            return False
    
    def _build_windows_native(self, native_dir: Path) -> bool:
        """Build Windows native components"""
        try:
            # Build C components
            c_sources = list(native_dir.glob("*.c"))
            for source in c_sources:
                output = self.build_dir / f"{source.stem}.dll"
                cmd = [
                    "cl", "/LD", "/Fe:", str(output),
                    str(source), "advapi32.lib", "user32.lib", "ws2_32.lib"
                ]
                if not self._run_command(cmd, "C compiler"):
                    return False
            
            # Build Rust components
            rust_projects = list(native_dir.glob("*.rs"))
            for project in rust_projects:
                cmd = ["cargo", "build", "--release"]
                if not self._run_command(cmd, "Rust compiler", cwd=native_dir):
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Windows native build failed: {e}")
            return False

    def _run_command(self, cmd, description, cwd=None) -> bool:
        """Run command with comprehensive error handling"""
        try:
            print(f"   {description}: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=cwd or self.project_root
            )
            
            if result.returncode != 0:
                print(f"   ❌ Error: {result.stderr}")
                return False
            
            return True
            
        except FileNotFoundError as e:
            print(f"   ❌ {description} not found: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Command failed: {e}")
            return False