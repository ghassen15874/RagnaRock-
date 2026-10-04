#!/usr/bin/env python3
"""
Python Formatter
"""

class PythonFormatter:
    def format(self, payload):
        """Format as Python script"""
        return f"""#!/usr/bin/env python3
# PySploit Generated Payload
{payload}
"""