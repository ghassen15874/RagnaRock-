import os
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

class Reporter:
    def __init__(self, db):
        self.db = db
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'reporting', 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _get_report_context(self, workspace):
        """Prepare validated data context for templates, ensuring cross-workspace isolation."""
        # The database query explicitly filters by workspace, enforcing isolation at the query level.
        hosts = self.db.get_hosts(workspace)
        
        context = {
            "workspace": workspace,
            "generation_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "metadata_source": "RagnaRok Core DB Engine",
            "total_hosts": len(hosts),
            "up_hosts": 0,
            "total_services": 0,
            "hosts": []
        }
        
        for host in hosts:
            host_id, ws, ip, mac, os_name, status, created, updated = host
            
            # Additional validation: strictly ensure host belongs to the requested workspace
            if ws != workspace:
                continue
                
            if str(status).lower() == "up":
                context["up_hosts"] += 1
                
            host_data = {
                "ip": ip,
                "status": status or "unknown",
                "mac": mac,
                "os": os_name,
                "services": []
            }
            
            # Services are fetched by host_id. Since host_id was validated to belong to the workspace, this is safe.
            services = self.db.get_services(host_id)
            context["total_services"] += len(services)
            
            for svc in services:
                # Based on the schema: id, host_id, port, protocol, name, state, info, created_at, updated_at
                # Note: `name` is index 4, `state` is index 5
                svc_id, hid, port, proto, name, state, info, sc, su = svc
                host_data["services"].append({
                    "port": port,
                    "protocol": proto,
                    "name": name,
                    "state": state or "unknown"
                })
            
            context["hosts"].append(host_data)
            
        return context

    def generate_html(self, workspace, output_file):
        """Generate an HTML report using Jinja2 template"""
        context = self._get_report_context(workspace)
        template = self.env.get_template("report.html")
        html_content = template.render(**context)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return True

    def generate_markdown(self, workspace, output_file):
        """Generate a Markdown report using Jinja2 template"""
        context = self._get_report_context(workspace)
        template = self.env.get_template("report.md")
        md_content = template.render(**context)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        return True

    def generate_json(self, workspace, output_file):
        """Generate a JSON report for a workspace"""
        context = self._get_report_context(workspace)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=4)
            
        return True
