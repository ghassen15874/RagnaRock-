import sys
import os
from colorama import init, Fore, Style

# Initialize colorama, auto-strips colors if output is not a terminal
init(autoreset=True)

class OutputFormatter:
    """Unified output formatting system for the framework"""
    
    def __init__(self):
        # Support terminals that don't support color by checking if we're in a TTY
        self.use_colors = sys.stdout.isatty() and os.getenv('TERM') != 'dumb'
        
    def _color(self, text, color):
        if not self.use_colors:
            return text
        return f"{color}{text}{Style.RESET_ALL}"

    def print_success(self, msg):
        prefix = self._color("[+]", Fore.GREEN)
        print(f"{prefix} {msg}")

    def print_error(self, msg, hint=None):
        prefix = self._color("[-]", Fore.RED)
        print(f"{prefix} {msg}")
        if hint:
            hint_prefix = self._color("[!]", Fore.YELLOW)
            print(f"{hint_prefix} Hint: {hint}")

    def print_warning(self, msg):
        prefix = self._color("[!]", Fore.YELLOW)
        print(f"{prefix} {msg}")

    def print_info(self, msg):
        prefix = self._color("[*]", Fore.BLUE)
        print(f"{prefix} {msg}")

    def print_table(self, title, headers, rows):
        """
        Prints a formatted table.
        headers: list of strings
        rows: list of lists (each sublist is a row)
        """
        if title:
            print(f"\n{self._color(title, Fore.CYAN)}")
            print("=" * 60)
            
        if not rows:
            self.print_warning("No data available.")
            print()
            return
            
        # Calculate column widths
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, item in enumerate(row):
                # Ensure we don't print sensitive data (e.g. raw passwords) 
                # This is a generic safeguard; specific scrubbing should happen before passing to print_table
                item_str = str(item)
                if len(item_str) > col_widths[i]:
                    col_widths[i] = len(item_str)
                    
        # Print headers
        header_row = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
        print(header_row)
        print("-" * len(header_row))
        
        # Print rows
        for row in rows:
            row_str = " | ".join(str(item).ljust(w) for item, w in zip(row, col_widths))
            print(row_str)
        print()
