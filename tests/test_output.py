import unittest
import sys
from core.output import OutputFormatter
from colorama import Fore

class TestOutputFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = OutputFormatter()
        # Force non-colors for predictable testing if needed, but we can test logic
        self.formatter.use_colors = False

    def test_print_success(self):
        # We just want to ensure it doesn't crash
        try:
            self.formatter.print_success("Test success")
        except Exception as e:
            self.fail(f"print_success raised Exception: {e}")

    def test_print_error(self):
        try:
            self.formatter.print_error("Test error", hint="Test hint")
        except Exception as e:
            self.fail(f"print_error raised Exception: {e}")

    def test_print_table(self):
        headers = ["ID", "Name", "Status"]
        rows = [
            [1, "Target A", "Active"],
            [2, "Target B", "Inactive"]
        ]
        try:
            self.formatter.print_table("Test Table", headers, rows)
        except Exception as e:
            self.fail(f"print_table raised Exception: {e}")

    def test_print_table_empty(self):
        headers = ["ID", "Name"]
        rows = []
        try:
            self.formatter.print_table("Empty Table", headers, rows)
        except Exception as e:
            self.fail(f"print_table raised Exception on empty data: {e}")

if __name__ == '__main__':
    unittest.main()
