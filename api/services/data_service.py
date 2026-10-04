import sqlite3
from typing import List, Dict, Any, Optional
from api.services.framework_service import FrameworkService

class DataService:
    @staticmethod
    def get_db_path():
        return FrameworkService.get_db().db_path

    @classmethod
    def get_hosts(
        cls, 
        workspace: str, 
        limit: int = 100, 
        offset: int = 0, 
        sort_by: str = "id", 
        sort_desc: bool = False,
        status_filter: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        
        valid_sort_cols = {"id", "ip_address", "os_name", "status", "created_at"}
        if sort_by not in valid_sort_cols:
            sort_by = "id"
            
        direction = "DESC" if sort_desc else "ASC"
        
        query = "SELECT id, workspace, ip_address, mac_address, os_name, status FROM hosts WHERE workspace = ?"
        params = [workspace]
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
            
        # Count total
        count_query = query.replace("SELECT id, workspace, ip_address, mac_address, os_name, status", "SELECT COUNT(*)")
        
        query += f" ORDER BY {sort_by} {direction} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(cls.get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(count_query, params[:-2])
            total = cursor.fetchone()[0]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = [dict(row) for row in rows]
            return result, total

    @classmethod
    def get_host_by_id(cls, host_id: int, workspace: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(cls.get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, workspace, ip_address, mac_address, os_name, status FROM hosts WHERE id = ? AND workspace = ?", 
                (host_id, workspace)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @classmethod
    def get_services(
        cls, 
        host_id: int, 
        workspace: str,
        limit: int = 100, 
        offset: int = 0, 
        sort_by: str = "port", 
        sort_desc: bool = False,
        protocol_filter: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        
        # Verify host belongs to workspace
        if not cls.get_host_by_id(host_id, workspace):
            return [], 0
            
        valid_sort_cols = {"id", "port", "protocol", "service_name", "state"}
        if sort_by not in valid_sort_cols:
            sort_by = "port"
            
        direction = "DESC" if sort_desc else "ASC"
        
        query = "SELECT id, host_id, port, protocol, service_name, state FROM services WHERE host_id = ?"
        params = [host_id]
        
        if protocol_filter:
            query += " AND protocol = ?"
            params.append(protocol_filter)
            
        count_query = query.replace("SELECT id, host_id, port, protocol, service_name, state", "SELECT COUNT(*)")
        
        query += f" ORDER BY {sort_by} {direction} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(cls.get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(count_query, params[:-2])
            total = cursor.fetchone()[0]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = [dict(row) for row in rows]
            return result, total

    @classmethod
    def get_service_by_id(cls, service_id: int, workspace: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(cls.get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Join with hosts to ensure workspace check
            cursor.execute('''
                SELECT s.id, s.host_id, s.port, s.protocol, s.service_name, s.state 
                FROM services s
                JOIN hosts h ON s.host_id = h.id
                WHERE s.id = ? AND h.workspace = ?
            ''', (service_id, workspace))
            row = cursor.fetchone()
            return dict(row) if row else None
