import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List

class HistoryAnalyzer:
    def __init__(self, db):
        self.db = db

    def save_snapshot(self, workspace: str, source: str, status: str = "completed") -> str:
        """Takes a snapshot of the current workspace state and saves it as a historical scan."""
        scan_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Ensure workspace exists (for foreign key constraint if enabled)
            cursor.execute("SELECT name FROM workspaces WHERE name = ?", (workspace,))
            if not cursor.fetchone():
                raise ValueError(f"Workspace {workspace} does not exist")

            # 1. Insert Scan Record
            cursor.execute(
                "INSERT INTO scans (scan_id, workspace, start_time, end_time, status, source) VALUES (?, ?, ?, ?, ?, ?)",
                (scan_id, workspace, now, now, status, source)
            )
            
            # 2. Insert Hosts Snapshot
            hosts = self.db.get_hosts(workspace)
            for host in hosts:
                host_id, ws, ip, mac, os_name, h_status, created, updated = host
                cursor.execute(
                    "INSERT INTO scan_hosts (scan_id, ip_address, mac_address, os_name, status) VALUES (?, ?, ?, ?, ?)",
                    (scan_id, ip, mac, os_name, h_status)
                )
                
                # 3. Insert Services Snapshot
                services = self.db.get_services(host_id)
                for svc in services:
                    svc_id, hid, port, proto, name, s_state, info, sc, su = svc
                    cursor.execute(
                        "INSERT INTO scan_services (scan_id, host_ip, port, protocol, name, state) VALUES (?, ?, ?, ?, ?, ?)",
                        (scan_id, ip, port, proto, name, s_state)
                    )
                    
            conn.commit()
            
        return scan_id

    def get_scan_history(self, workspace: str) -> List[Dict]:
        """Returns the timeline of scans for a workspace."""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM scans WHERE workspace = ? ORDER BY end_time DESC",
                (workspace,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def compare_scans(self, workspace: str, old_scan_id: str, new_scan_id: str) -> Dict[str, Any]:
        """Compares two historical scans and returns the differences."""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verify both scans belong to the requested workspace (Isolation Check)
            for s_id in (old_scan_id, new_scan_id):
                cursor.execute("SELECT workspace FROM scans WHERE scan_id = ?", (s_id,))
                row = cursor.fetchone()
                if not row or row['workspace'] != workspace:
                    raise ValueError(f"Scan {s_id} not found or does not belong to workspace {workspace}")

            # Fetch Old Data
            cursor.execute("SELECT * FROM scan_hosts WHERE scan_id = ?", (old_scan_id,))
            old_hosts = {row['ip_address']: dict(row) for row in cursor.fetchall()}
            
            cursor.execute("SELECT * FROM scan_services WHERE scan_id = ?", (old_scan_id,))
            old_services = {(row['host_ip'], row['port'], row['protocol']): dict(row) for row in cursor.fetchall()}
            
            # Fetch New Data
            cursor.execute("SELECT * FROM scan_hosts WHERE scan_id = ?", (new_scan_id,))
            new_hosts = {row['ip_address']: dict(row) for row in cursor.fetchall()}
            
            cursor.execute("SELECT * FROM scan_services WHERE scan_id = ?", (new_scan_id,))
            new_services = {(row['host_ip'], row['port'], row['protocol']): dict(row) for row in cursor.fetchall()}

        # Analysis Logic
        report = {
            "workspace": workspace,
            "old_scan_id": old_scan_id,
            "new_scan_id": new_scan_id,
            "hosts": {
                "new": [],
                "removed": [],
                "state_changed": []
            },
            "services": {
                "new": [],
                "removed": [],
                "state_changed": []
            }
        }

        # Compare Hosts
        for ip in new_hosts:
            if ip not in old_hosts:
                report["hosts"]["new"].append(ip)
            elif new_hosts[ip]["status"] != old_hosts[ip]["status"]:
                report["hosts"]["state_changed"].append({
                    "ip": ip,
                    "old_status": old_hosts[ip]["status"],
                    "new_status": new_hosts[ip]["status"]
                })
                
        for ip in old_hosts:
            if ip not in new_hosts:
                report["hosts"]["removed"].append(ip)

        # Compare Services
        for key in new_services:
            if key not in old_services:
                report["services"]["new"].append(new_services[key])
            elif new_services[key]["state"] != old_services[key]["state"]:
                report["services"]["state_changed"].append({
                    "service": new_services[key],
                    "old_state": old_services[key]["state"],
                    "new_state": new_services[key]["state"]
                })
                
        for key in old_services:
            if key not in new_services:
                report["services"]["removed"].append(old_services[key])
                
        return report
