#!/usr/bin/env python3
"""
Comprehensive audit logging for C2 operations
"""
import asyncio
import time
import json
import logging
import logging.handlers
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from contextlib import asynccontextmanager
import aiofiles
import gzip
import hashlib
from pathlib import Path

class LogLevel(Enum):
    """Log levels for audit events"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    SECURITY = 60  # Special level for security events

class EventType(Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_FAILED = "mfa_failed"
    PASSWORD_CHANGED = "password_changed"
    
    # Operator actions
    AGENT_CONNECTED = "agent_connected"
    AGENT_DISCONNECTED = "agent_disconnected"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    COMMAND_EXECUTED = "command_executed"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGED = "config_changed"
    BACKUP_CREATED = "backup_created"
    
    # Security events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_EXPORT = "data_export"
    INTEGRITY_CHECK = "integrity_check"

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: EventType
    timestamp: float
    operator: str
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    severity: LogLevel
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data

class AuditLogger:
    """
    Comprehensive audit logging system for C2 operations
    """
    
    def __init__(self, log_directory: str = "logs", db_path: str = "audit.db"):
        self.log_directory = Path(log_directory)
        self.db_path = db_path
        self.log_directory.mkdir(exist_ok=True)
        
        # Initialize logging systems
        self._setup_file_logging()
        self._setup_database()
        self._setup_console_logging()
        
        # Security features
        self.log_retention_days = 90
        self.max_log_size_mb = 100
        self.encryption_key = None
        
        # Statistics
        self.stats = {
            'events_logged': 0,
            'errors': 0,
            'last_cleanup': time.time()
        }
    
    def _setup_file_logging(self):
        """Setup file-based logging"""
        # JSON log file for structured logging
        self.json_handler = logging.handlers.RotatingFileHandler(
            self.log_directory / "audit.json",
            maxBytes=self.max_log_size_mb * 1024 * 1024,
            backupCount=10
        )
        
        # Security log file for critical events
        self.security_handler = logging.handlers.RotatingFileHandler(
            self.log_directory / "security.log",
            maxBytes=self.max_log_size_mb * 1024 * 1024,
            backupCount=5
        )
        self.security_handler.setLevel(logging.WARNING)
        
        # Setup formatters
        json_formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "event": %(message)s}'
        )
        self.json_handler.setFormatter(json_formatter)
        
        security_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        self.security_handler.setFormatter(security_formatter)
    
    def _setup_database(self):
        """Setup SQLite database for audit events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    operator TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    agent_id TEXT,
                    task_id TEXT,
                    severity INTEGER NOT NULL,
                    details TEXT NOT NULL
                )
            ''')
            
            # Create indexes for efficient querying
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_operator ON audit_events(operator)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_id ON audit_events(agent_id)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Database setup failed: {e}")
    
    def _setup_console_logging(self):
        """Setup console logging for development"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('audit_logger')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(self.json_handler)
        self.logger.addHandler(self.security_handler)
    
    async def log_event(self, event: AuditEvent):
        """Log audit event to all systems"""
        try:
            # Generate event ID if not provided
            if not event.event_id:
                event.event_id = self._generate_event_id(event)
            
            # Log to file system
            await self._log_to_file(event)
            
            # Log to database
            await self._log_to_database(event)
            
            # Log to console (for development)
            self._log_to_console(event)
            
            # Update statistics
            self.stats['events_logged'] += 1
            
            # Perform periodic cleanup
            if time.time() - self.stats['last_cleanup'] > 86400:  # 24 hours
                await self.cleanup_old_logs()
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Failed to log event: {e}")
    
    async def _log_to_file(self, event: AuditEvent):
        """Log event to JSON file"""
        try:
            log_entry = event.to_dict()
            
            # Use appropriate log level
            if event.severity == LogLevel.SECURITY:
                log_method = self.logger.warning
            else:
                log_method = getattr(self.logger, event.severity.name.lower())
            
            log_method(json.dumps(log_entry))
            
        except Exception as e:
            self.logger.error(f"File logging failed: {e}")
    
    async def _log_to_database(self, event: AuditEvent):
        """Log event to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_events 
                (event_id, event_type, timestamp, operator, ip_address, user_agent, 
                 session_id, agent_id, task_id, severity, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.event_type.value,
                event.timestamp,
                event.operator,
                event.ip_address,
                event.user_agent,
                event.session_id,
                event.agent_id,
                event.task_id,
                event.severity.value,
                json.dumps(event.details)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database logging failed: {e}")
    
    def _log_to_console(self, event: AuditEvent):
        """Log event to console"""
        try:
            message = f"{event.event_type.value} - {event.operator} - {event.details}"
            
            if event.severity == LogLevel.SECURITY:
                self.logger.warning(f"SECURITY: {message}")
            else:
                level_name = event.severity.name.lower()
                getattr(self.logger, level_name)(message)
                
        except Exception as e:
            print(f"Console logging failed: {e}")
    
    def _generate_event_id(self, event: AuditEvent) -> str:
        """Generate unique event ID"""
        content = f"{event.event_type.value}{event.timestamp}{event.operator}{event.ip_address}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def query_events(self, 
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None,
                         operator: Optional[str] = None,
                         event_type: Optional[EventType] = None,
                         agent_id: Optional[str] = None,
                         severity: Optional[LogLevel] = None,
                         limit: int = 1000) -> List[AuditEvent]:
        """Query audit events from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if operator:
                query += " AND operator = ?"
                params.append(operator)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)
            
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
            
            if severity:
                query += " AND severity >= ?"
                params.append(severity.value)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event = AuditEvent(
                    event_id=row[0],
                    event_type=EventType(row[1]),
                    timestamp=row[2],
                    operator=row[3],
                    ip_address=row[4],
                    user_agent=row[5],
                    session_id=row[6],
                    agent_id=row[7],
                    task_id=row[8],
                    severity=LogLevel(row[9]),
                    details=json.loads(row[10])
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"Event query failed: {e}")
            return []
    
    async def get_operator_activity(self, operator: str, days: int = 30) -> Dict[str, Any]:
        """Get operator activity summary"""
        end_time = time.time()
        start_time = end_time - (days * 86400)
        
        events = await self.query_events(
            start_time=start_time,
            end_time=end_time,
            operator=operator
        )
        
        activity = {
            'total_events': len(events),
            'event_types': {},
            'first_activity': None,
            'last_activity': None,
            'sessions': set(),
            'agents_interacted': set()
        }
        
        for event in events:
            # Count event types
            event_type = event.event_type.value
            activity['event_types'][event_type] = activity['event_types'].get(event_type, 0) + 1
            
            # Track sessions
            if event.session_id:
                activity['sessions'].add(event.session_id)
            
            # Track agents
            if event.agent_id:
                activity['agents_interacted'].add(event.agent_id)
            
            # Track time range
            if not activity['first_activity'] or event.timestamp < activity['first_activity']:
                activity['first_activity'] = event.timestamp
            
            if not activity['last_activity'] or event.timestamp > activity['last_activity']:
                activity['last_activity'] = event.timestamp
        
        activity['sessions'] = list(activity['sessions'])
        activity['agents_interacted'] = list(activity['agents_interacted'])
        
        return activity
    
    async def detect_suspicious_activity(self, operator: str, window_minutes: int = 5) -> List[AuditEvent]:
        """Detect suspicious activity patterns"""
        end_time = time.time()
        start_time = end_time - (window_minutes * 60)
        
        events = await self.query_events(
            start_time=start_time,
            end_time=end_time,
            operator=operator
        )
        
        suspicious_events = []
        
        # Check for multiple failed logins
        failed_logins = [e for e in events if e.event_type == EventType.LOGIN_FAILED]
        if len(failed_logins) >= 3:
            suspicious_events.extend(failed_logins)
        
        # Check for rapid succession of sensitive operations
        sensitive_events = [e for e in events if e.severity in [LogLevel.SECURITY, LogLevel.ERROR]]
        if len(sensitive_events) >= 10:
            suspicious_events.extend(sensitive_events)
        
        # Check for unusual hours (if known working hours are defined)
        # This is a simplified example
        for event in events:
            event_time = time.localtime(event.timestamp)
            if event_time.tm_hour < 6 or event_time.tm_hour > 22:  # 6 AM to 10 PM
                if event.event_type in [EventType.TASK_CREATED, EventType.COMMAND_EXECUTED]:
                    suspicious_events.append(event)
        
        return suspicious_events
    
    async def export_logs(self, start_time: float, end_time: float, 
                         output_path: str, compress: bool = True) -> bool:
        """Export logs for specified time range"""
        try:
            events = await self.query_events(start_time=start_time, end_time=end_time, limit=100000)
            
            export_data = {
                'export_time': time.time(),
                'time_range': {
                    'start': start_time,
                    'end': end_time
                },
                'total_events': len(events),
                'events': [event.to_dict() for event in events]
            }
            
            if compress:
                output_path += '.gz'
                async with aiofiles.open(output_path, 'wb') as f:
                    compressed_data = gzip.compress(json.dumps(export_data).encode())
                    await f.write(compressed_data)
            else:
                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(json.dumps(export_data, indent=2))
            
            # Log the export operation
            export_event = AuditEvent(
                event_type=EventType.DATA_EXPORT,
                timestamp=time.time(),
                operator="system",
                ip_address="127.0.0.1",
                user_agent="audit_logger",
                details={
                    'export_path': output_path,
                    'time_range': {'start': start_time, 'end': end_time},
                    'event_count': len(events),
                    'compressed': compress
                },
                severity=LogLevel.INFO
            )
            await self.log_event(export_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Log export failed: {e}")
            return False
    
    async def cleanup_old_logs(self):
        """Cleanup logs older than retention period"""
        try:
            cutoff_time = time.time() - (self.log_retention_days * 86400)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM audit_events WHERE timestamp < ?', (cutoff_time,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            # Log the cleanup operation
            cleanup_event = AuditEvent(
                event_type=EventType.SYSTEM_STARTUP,  # Reusing event type
                timestamp=time.time(),
                operator="system",
                ip_address="127.0.0.1",
                user_agent="audit_logger",
                details={
                    'action': 'log_cleanup',
                    'cutoff_time': cutoff_time,
                    'deleted_records': deleted_count
                },
                severity=LogLevel.INFO
            )
            await self.log_event(cleanup_event)
            
            self.stats['last_cleanup'] = time.time()
            
            self.logger.info(f"Cleaned up {deleted_count} old audit records")
            
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total event count
            cursor.execute('SELECT COUNT(*) FROM audit_events')
            total_events = cursor.fetchone()[0]
            
            # Get events by type
            cursor.execute('''
                SELECT event_type, COUNT(*) 
                FROM audit_events 
                GROUP BY event_type 