import os
from datetime import datetime

class Reporter:
    def __init__(self, db):
        self.db = db

    def generate_markdown(self, workspace, output_file):
        """Generate a Markdown report for a workspace"""
        hosts = self.db.get_hosts(workspace)
        
        with open(output_file, 'w') as f:
            f.write(f"# RagnaRok Security Assessment Report\n\n")
            f.write(f"**Workspace:** {workspace}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## Executive Summary\n")
            f.write(f"This report contains the security assessment results for workspace `{workspace}`.\n")
            f.write(f"Total Hosts Discovered: {len(hosts)}\n\n")
            
            f.write(f"## Discovered Hosts & Services\n\n")
            
            if not hosts:
                f.write("*No hosts found.*\n")
                return True
                
            for host in hosts:
                host_id, ws, ip, mac, os_name, status, created, updated = host
                f.write(f"### Target: {ip}\n")
                f.write(f"- **Status**: {status}\n")
                if mac:
                    f.write(f"- **MAC Address**: {mac}\n")
                if os_name:
                    f.write(f"- **OS**: {os_name}\n")
                    
                services = self.db.get_services(host_id)
                f.write(f"\n#### Services\n")
                if not services:
                    f.write("*No open services found.*\n\n")
                    continue
                    
                f.write("| Port | Protocol | Service | State |\n")
                f.write("|------|----------|---------|-------|\n")
                for svc in services:
                    svc_id, hid, port, proto, name, state, info, sc, su = svc
                    f.write(f"| {port} | {proto} | {name or 'unknown'} | {state} |\n")
                f.write("\n")
                
        return True
        
    def generate_html(self, workspace, output_file):
        """Generate an HTML report for a workspace"""
        hosts = self.db.get_hosts(workspace)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>RagnaRok Report - {workspace}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2980b9; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .summary {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .host-card {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 5px solid #e74c3c; }}
    </style>
</head>
<body>
    <h1>RagnaRok Security Assessment Report</h1>
    <div class="summary">
        <h2>Executive Summary</h2>
        <p><strong>Workspace:</strong> {workspace}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Hosts Discovered:</strong> {len(hosts)}</p>
    </div>
    
    <h2>Discovered Hosts & Services</h2>
"""
        if not hosts:
            html += "<p><em>No hosts found.</em></p>"
        else:
            for host in hosts:
                host_id, ws, ip, mac, os_name, status, created, updated = host
                html += f"""
    <div class="host-card">
        <h3>Target: {ip}</h3>
        <p><strong>Status:</strong> {status} {f'| <strong>MAC:</strong> {mac}' if mac else ''} {f'| <strong>OS:</strong> {os_name}' if os_name else ''}</p>
        <h4>Services</h4>
"""
                services = self.db.get_services(host_id)
                if not services:
                    html += "<p><em>No open services found.</em></p>"
                else:
                    html += """
        <table>
            <tr>
                <th>Port</th>
                <th>Protocol</th>
                <th>Service</th>
                <th>State</th>
            </tr>
"""
                    for svc in services:
                        svc_id, hid, port, proto, name, state, info, sc, su = svc
                        html += f"""
            <tr>
                <td>{port}</td>
                <td>{proto}</td>
                <td>{name or 'unknown'}</td>
                <td>{state}</td>
            </tr>"""
                    html += """
        </table>"""
                html += """
    </div>"""
                
        html += """
</body>
</html>"""
        
        with open(output_file, 'w') as f:
            f.write(html)
            
        return True

    def generate_json(self, workspace, output_file):
        """Generate a JSON report for a workspace"""
        import json
        hosts = self.db.get_hosts(workspace)
        report_data = {
            "workspace": workspace,
            "date": datetime.now().isoformat(),
            "total_hosts": len(hosts),
            "hosts": []
        }
        
        for host in hosts:
            host_id, ws, ip, mac, os_name, status, created, updated = host
            host_data = {
                "ip": ip,
                "status": status,
                "mac": mac,
                "os": os_name,
                "services": []
            }
            
            services = self.db.get_services(host_id)
            for svc in services:
                svc_id, hid, port, proto, name, state, info, sc, su = svc
                host_data["services"].append({
                    "port": port,
                    "protocol": proto,
                    "name": name,
                    "state": state
                })
            
            report_data["hosts"].append(host_data)
            
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=4)
            
        return True
