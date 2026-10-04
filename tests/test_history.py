import unittest
import os
from core.session_db import SessionDatabase
from core.history import HistoryAnalyzer

class TestHistoryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_history.db"
        self.db = SessionDatabase(self.db_path)
        self.analyzer = HistoryAnalyzer(self.db)
        
        # Clear tables
        with __import__('sqlite3').connect(self.db_path) as conn:
            conn.execute("DELETE FROM scan_services")
            conn.execute("DELETE FROM scan_hosts")
            conn.execute("DELETE FROM scans")
            conn.execute("DELETE FROM services")
            conn.execute("DELETE FROM hosts")
            conn.execute("DELETE FROM workspaces")
            
        self.db.add_workspace("ws1")
        self.db.add_workspace("ws2")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_snapshot(self):
        self.db.add_host("ws1", "10.0.0.1", os_name="Linux", status="up")
        h_id = self.db.get_hosts("ws1")[0][0]
        self.db.add_service(h_id, 22, "tcp", "ssh", "open")
        
        scan_id = self.analyzer.save_snapshot("ws1", "Nmap Scan")
        
        history = self.analyzer.get_scan_history("ws1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["scan_id"], scan_id)
        self.assertEqual(history[0]["source"], "Nmap Scan")
        self.assertEqual(history[0]["status"], "completed")

    def test_compare_scans(self):
        # 1. State A (Initial Scan)
        self.db.add_host("ws1", "10.0.0.1", os_name="Linux", status="up")
        self.db.add_host("ws1", "10.0.0.2", os_name="Windows", status="down")
        h1_id = self.db.get_hosts("ws1")[0][0]
        self.db.add_service(h1_id, 22, "tcp", "ssh", "open")
        self.db.add_service(h1_id, 80, "tcp", "http", "open")
        
        scan_1 = self.analyzer.save_snapshot("ws1", "Initial Scan")
        
        # 2. State B (Updated State)
        # 10.0.0.2 comes up
        self.db.add_host("ws1", "10.0.0.2", os_name="Windows", status="up")
        h2_id = self.db.get_hosts("ws1")[1][0]
        
        # 10.0.0.1 loses port 80 but gains 443
        with __import__('sqlite3').connect(self.db_path) as conn:
            # Manually delete port 80 since db module might not have remove_service
            conn.execute("DELETE FROM services WHERE host_id = ? AND port = 80", (h1_id,))
        self.db.add_service(h1_id, 443, "tcp", "https", "open")
        
        # Port 22 closes
        self.db.add_service(h1_id, 22, "tcp", "ssh", "closed")
        
        # New host appears
        self.db.add_host("ws1", "10.0.0.3", status="up")
        
        scan_2 = self.analyzer.save_snapshot("ws1", "Daily Scan")
        
        # 3. Compare
        report = self.analyzer.compare_scans("ws1", scan_1, scan_2)
        
        # Hosts assertions
        self.assertIn("10.0.0.3", report["hosts"]["new"])
        self.assertEqual(len(report["hosts"]["removed"]), 0)
        self.assertEqual(len(report["hosts"]["state_changed"]), 1)
        self.assertEqual(report["hosts"]["state_changed"][0]["ip"], "10.0.0.2")
        self.assertEqual(report["hosts"]["state_changed"][0]["old_status"], "down")
        self.assertEqual(report["hosts"]["state_changed"][0]["new_status"], "up")
        
        # Services assertions
        # new: 443
        new_svc_ports = [s["port"] for s in report["services"]["new"]]
        self.assertIn(443, new_svc_ports)
        
        # removed: 80
        rem_svc_ports = [s["port"] for s in report["services"]["removed"]]
        self.assertIn(80, rem_svc_ports)
        
        # changed: 22
        self.assertEqual(len(report["services"]["state_changed"]), 1)
        changed_svc = report["services"]["state_changed"][0]
        self.assertEqual(changed_svc["service"]["port"], 22)
        self.assertEqual(changed_svc["old_state"], "open")
        self.assertEqual(changed_svc["new_state"], "closed")

    def test_workspace_isolation(self):
        # Scan in ws1
        self.db.add_host("ws1", "10.0.0.1", status="up")
        scan_1 = self.analyzer.save_snapshot("ws1", "Scan 1")
        
        # Scan in ws2
        self.db.add_host("ws2", "192.168.1.1", status="up")
        scan_2 = self.analyzer.save_snapshot("ws2", "Scan 2")
        
        # Attempt to compare ws1 scan with ws2 scan
        with self.assertRaises(ValueError):
            self.analyzer.compare_scans("ws1", scan_1, scan_2)

if __name__ == '__main__':
    unittest.main()
