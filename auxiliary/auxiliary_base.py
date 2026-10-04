#!/usr/bin/env python3
"""
Base class for auxiliary modules
"""

class AuxiliaryBase:
    """Base class for all auxiliary modules"""
    def __init__(self):
        self.name = "base/auxiliary"
        self.description = "Base auxiliary class"
        self.author = "PySploit Framework"
        self.references = []
        self.options = {}
        self.framework = None  # Set by framework on load

    def run(self):
        """Main method to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement run()")

    def get_option(self, name):
        """Safely get option value, falling back to default (fixes B9).

        Returns None for unknown option names without raising KeyError.
        """
        if name not in self.options:
            return None
        opt = self.options[name]
        if 'value' in opt:
            return opt['value']
        return opt.get('default')

    def set_framework(self, framework):
        """Set framework reference"""
        self.framework = framework