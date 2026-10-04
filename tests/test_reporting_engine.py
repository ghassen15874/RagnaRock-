import unittest
import os
import json
from datetime import datetime
from core.session_db import SessionDatabase
from core.reporter import Reporter

class TestReportingEngine(unittest.TestCase):
    def setUp(self):
        # Create an in-memory or temporary DB
        self.db = SessionDatabase("test_reporting.db")
        self.reporter = Reporter(self.db)
        
        # Clear existing data
        with __import__('sqlite3').connect(self.db.db_path) as conn:
            conn.execute("DELETE FROM hosts")
            conn.execute("DELETE FROM services")
            
        # Add Workspace 1 data (Target Workspace)
        self.db.add_workspace("ws1")
        self.db.add_host("ws1", "10.0.0.1", os_name="Linux", status="up")
        self.db.add_host("ws1", "10.0.0.2", os_name="Windows", status="down")
        
        h1 = self.db.get_hosts("ws1")[0][0] # ID of 10.0.0.1
        h2 = self.db.get_hosts("ws1")[1][0] # ID of 10.0.0.2
        
        self.db.add_service(h1, 22, "tcp", "ssh", "open")
        self.db.add_service(h1, 80, "tcp", "http", "open")
        self.db.add_service(h2, 445, "tcp", "smb", "closed")
        
        # Add Workspace 2 data (Should not leak into ws1 reports)
        self.db.add_workspace("ws2")
        self.db.add_host("ws2", "192.168.1.100", status="up")
        h3 = self.db.get_hosts("ws2")[0][0]
        self.db.add_service(h3, 3306, "tcp", "mysql", "open")
        
        # Create reports directory if not exists
        os.makedirs("reports", exist_ok=True)

    def tearDown(self):
        if os.path.exists("test_reporting.db"):
            os.remove("test_reporting.db")

    def test_report_context_generation(self):
        context = self.reporter._get_report_context("ws1")
        
        self.assertEqual(context["workspace"], "ws1")
        self.assertEqual(context["total_hosts"], 2)
        self.assertEqual(context["up_hosts"], 1)
        self.assertEqual(context["total_services"], 3)
        self.assertEqual(len(context["hosts"]), 2)
        
        # Ensure ws2 data is not present (No 192.168.1.100, no port 3306)
        for h in context["hosts"]:
            self.assertNotEqual(h["ip"], "192.168.1.100")
            for s in h["services"]:
                self.assertNotEqual(s["port"], 3306)

    def test_generate_json_report(self):
        output_file = "reports/sample_report.json"
        success = self.reporter.generate_json("ws1", output_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data["workspace"], "ws1")
        self.assertEqual(data["total_hosts"], 2)

    def test_generate_markdown_report(self):
        output_file = "reports/sample_report.md"
        success = self.reporter.generate_markdown("ws1", output_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            content = f.read()
            
        self.assertIn("Workspace:** `ws1`", content)
        self.assertIn("Total Hosts:** 2", content)
        self.assertIn("Target: 10.0.0.1", content)
        self.assertIn("Target: 10.0.0.2", content)
        self.assertNotIn("192.168.1.100", content) # Cross-workspace check

    def test_generate_html_report(self):
        output_file = "reports/sample_report.html"
        success = self.reporter.generate_html("ws1", output_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            content = f.read()
            
        self.assertIn("<title>RagnaRok Security Assessment Report - ws1</title>", content)
        self.assertIn("Total Hosts</h3>", content)
        self.assertIn('<div class="number">2</div>', content)
        self.assertIn("10.0.0.1", content)
        self.assertNotIn("192.168.1.100", content) # Cross-workspace check

if __name__ == '__main__':
    unittest.main()
