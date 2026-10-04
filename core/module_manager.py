#!/usr/bin/env python3
"""
Enhanced Module Manager - Auto-discovers module options dynamically
"""

import inspect
from typing import Dict, Any, List

class ModuleManager:
    def __init__(self, framework):
        self.framework = framework
        self.current_module = None
        self.module_type = None
        self.module_name = None
        
    def use(self, module_path):
        """Set current module with flexible path parsing"""
        # Handle both formats: "exploit/vsftpd_234" and "vsftpd_234"
        parts = module_path.split('/')
        
        if len(parts) == 1:
            # Single name - try to auto-detect type
            module_name = parts[0].lower()
            return self._auto_detect_module(module_name)
        else:
            # Full path like "exploit/vsftpd_234"
            module_type = parts[0].lower()
            module_name = parts[-1].lower()
            return self._set_module_by_type(module_type, module_name)
    
    def _auto_detect_module(self, module_name):
        """Auto-detect module type"""
        # Check exploits first
        if module_name in self.framework.exploits:
            self.current_module = self.framework.exploits[module_name]
            self.module_type = 'exploit'
            self.module_name = module_name
            return True, f"Using exploit: {module_name}"
        
        # Check auxiliary modules
        if module_name in self.framework.auxiliary:
            self.current_module = self.framework.auxiliary[module_name]
            self.module_type = 'auxiliary' 
            self.module_name = module_name
            return True, f"Using auxiliary: {module_name}"
        
        return False, f"Module not found: {module_name}"
    
    def _set_module_by_type(self, module_type, module_name):
        """Set module by specific type"""
        if module_type == 'exploit':
            if module_name in self.framework.exploits:
                self.current_module = self.framework.exploits[module_name]
                self.module_type = 'exploit'
                self.module_name = module_name
                return True, f"Using exploit: {module_name}"
        
        elif module_type == 'auxiliary':
            if module_name in self.framework.auxiliary:
                self.current_module = self.framework.auxiliary[module_name]
                self.module_type = 'auxiliary'
                self.module_name = module_name
                return True, f"Using auxiliary: {module_name}"
        
        return False, f"Module not found: {module_type}/{module_name}"
    
    def discover_options(self):
        """Dynamically discover what options the module actually uses"""
        if not self.current_module:
            return "No module selected"
        
        # Get the actual options from the module
        if hasattr(self.current_module, 'options') and self.current_module.options:
            return self._format_options(self.current_module.options)
        else:
            return self._analyze_module_usage()
    
    def _format_options(self, options_dict):
        """Format the module's options for display"""
        output = f"\nModule options ({self.module_type}/{self.module_name}):\n\n"
        output += "   Name           Current Setting  Required  Description\n"
        output += "   ----           ---------------  --------  -----------\n"
        
        for opt_name, opt_info in options_dict.items():
            # Get current value safely
            current_value = ""
            if hasattr(self.current_module, 'get_option'):
                current_value = self.current_module.get_option(opt_name) or ""
            elif 'value' in opt_info:
                current_value = opt_info['value']
            elif 'default' in opt_info:
                current_value = opt_info['default']
            
            required = opt_info.get('required', False)
            description = opt_info.get('description', 'No description')
            
            # Format the output
            current_str = str(current_value)[:20]  # Limit length
            output += f"   {opt_name:<15} {current_str:<16} {'yes' if required else 'no':<9}  {description}\n"
        
        return output
    
    def _analyze_module_usage(self):
        """Analyze module to discover what options it actually uses"""
        # This would analyze the run() method to see what it accesses
        # For now, return a basic message
        return f"\nModule {self.module_name} doesn't have defined options.\nUse 'set' command to configure parameters directly."
    
    def set_option(self, name, value):
        """Set option for current module with flexible handling"""
        if not self.current_module:
            return False, "No module selected"
        
        # Convert name to uppercase for consistency
        name_upper = name.upper()
        
        # Try to set via options dictionary first
        if hasattr(self.current_module, 'options') and name_upper in self.current_module.options:
            opt_info = self.current_module.options[name_upper]
            
            # Type conversion based on option definition
            option_type = opt_info.get('type', 'string')
            converted_value = self._convert_value(value, option_type)
            
            # Update the option
            self.current_module.options[name_upper]['value'] = converted_value
            return True, f"{name} => {converted_value}"
        
        # If no options dict, try to set directly on module
        elif hasattr(self.current_module, 'set_option'):
            # Let the module handle the setting
            try:
                self.current_module.set_option(name, value)
                return True, f"{name} => {value}"
            except Exception as e:
                return False, f"Failed to set {name}: {e}"
        
        else:
            # Last resort: set as attribute
            try:
                setattr(self.current_module, name_upper, value)
                return True, f"{name} => {value}"
            except Exception as e:
                return False, f"Failed to set {name}: {e}"
    
    def _convert_value(self, value, value_type):
        """Convert value to appropriate type"""
        if value_type == 'int':
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
        elif value_type == 'bool':
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 'on', 'y')
            return bool(value)
        elif value_type == 'string':
            return str(value)
        else:
            return value
    
    def run(self):
        """Run the current module with proper framework setup"""
        if not self.current_module:
            return False, "No module selected"
        
        # Set framework reference if needed
        if hasattr(self.current_module, 'set_framework'):
            self.current_module.set_framework(self.framework)
        
        # Check if module has required options
        missing_required = self._check_required_options()
        if missing_required:
            return False, f"Missing required options: {', '.join(missing_required)}"
        
        try:
            # Run based on module type
            if self.module_type == 'exploit':
                # Get target from options
                target = self._get_option_value('RHOST') or self._get_option_value('TARGET') or 'unknown'
                payload = None
                
                # Run the exploit
                success = self.current_module.run(target, payload)
                return success, "Exploit completed successfully" if success else "Exploit failed"
            
            elif self.module_type == 'auxiliary':
                # Run auxiliary module
                success = self.current_module.run()
                return success, "Auxiliary module completed" if success else "Auxiliary module failed"
            
            else:
                return False, f"Unknown module type: {self.module_type}"
                
        except Exception as e:
            return False, f"Error running module: {e}"
    
    def _check_required_options(self):
        """Check for missing required options"""
        missing = []
        
        if hasattr(self.current_module, 'options'):
            for opt_name, opt_info in self.current_module.options.items():
                if opt_info.get('required', False):
                    current_value = self._get_option_value(opt_name)
                    if not current_value and 'default' not in opt_info:
                        missing.append(opt_name)
        
        return missing
    
    def _get_option_value(self, name):
        """Safely get option value using module's get_option method or direct access"""
        if hasattr(self.current_module, 'get_option'):
            return self.current_module.get_option(name)
        
        # Fallback: check options dict
        if hasattr(self.current_module, 'options') and name in self.current_module.options:
            opt_info = self.current_module.options[name]
            if 'value' in opt_info:
                return opt_info['value']
            elif 'default' in opt_info:
                return opt_info['default']
        
        return None
    
    def get_prompt(self):
        """Get context-aware prompt"""
        if not self.current_module:
            return "pysploit"
        
        # Use module name for prompt
        display_name = self.module_name
        if hasattr(self.current_module, 'name'):
            # Extract last part of path-style names
            display_name = self.current_module.name.split('/')[-1]
        
        return f"pysploit {self.module_type}({display_name})"
    
    def back(self):
        """Go back to main context"""
        self.current_module = None
        self.module_type = None
        self.module_name = None
        return "Back to main context"
    
    def get_module_info(self):
        """Get information about current module"""
        if not self.current_module:
            return "No module selected"
        
        info = f"\n       Name: {getattr(self.current_module, 'name', self.module_name)}"
        info += f"\n     Module: {self.module_type}/{self.module_name}"
        info += f"\nDescription: {getattr(self.current_module, 'description', 'No description')}"
        info += f"\n      Author: {getattr(self.current_module, 'author', 'Unknown')}"
        
        if hasattr(self.current_module, 'references') and self.current_module.references:
            info += f"\n References: {', '.join(self.current_module.references)}"
        
        return info