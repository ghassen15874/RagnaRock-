import logging
import logging.handlers
import os
import re
import uuid
import zipfile
import threading
from datetime import datetime

class SecretFilter(logging.Filter):
    """Filter to prevent sensitive data from appearing in logs"""
    def __init__(self):
        super().__init__()
        # Matches patterns like password=..., token:..., etc.
        self.secret_pattern = re.compile(
            r'(password|passwd|pwd|token|api_key|secret)\s*[:=]\s*([^\s,]+)',
            re.IGNORECASE
        )

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = self.secret_pattern.sub(r'\1=***MASKED***', record.msg)
        return True

class TraceFormatter(logging.Formatter):
    def format(self, record):
        # Inject trace_id if not present
        if not hasattr(record, 'trace_id'):
            record.trace_id = getattr(threading.current_thread(), 'trace_id', 'SYSTEM')
        return super().format(record)

class LoggerFactory:
    """Central logging factory with rotation and secret masking"""
    _loggers = {}
    _lock = threading.Lock()
    
    @staticmethod
    def setup(log_dir="~/.ragnarok/logs", log_level=logging.INFO):
        log_dir = os.path.expanduser(log_dir)
        os.makedirs(log_dir, exist_ok=True)
        
        # We will create two main log files: system.log and modules.log
        LoggerFactory._create_logger("system", os.path.join(log_dir, "system.log"), log_level)
        LoggerFactory._create_logger("modules", os.path.join(log_dir, "modules.log"), log_level)
        
    @staticmethod
    def _create_logger(name, file_path, log_level):
        with LoggerFactory._lock:
            logger = logging.getLogger(f"RagnaRok.{name}")
            logger.setLevel(log_level)
            
            # Avoid duplicate handlers if setup is called multiple times
            if not logger.handlers:
                # 5 MB max per file, keep 3 backups -> log rotation
                handler = logging.handlers.RotatingFileHandler(
                    file_path, maxBytes=5*1024*1024, backupCount=3
                )
                
                formatter = TraceFormatter(
                    '%(asctime)s | %(levelname)-8s | [%(trace_id)s] | %(message)s'
                )
                handler.setFormatter(formatter)
                handler.addFilter(SecretFilter())
                
                logger.addHandler(handler)
                LoggerFactory._loggers[name] = logger
            
            return logger

    @staticmethod
    def get_logger(name="system"):
        return LoggerFactory._loggers.get(name, logging.getLogger("RagnaRok.default"))

    @staticmethod
    def set_trace_id(trace_id=None):
        if not trace_id:
            trace_id = uuid.uuid4().hex[:8]
        threading.current_thread().trace_id = trace_id
        return trace_id

    @staticmethod
    def export_diagnostics(export_path, log_dir="~/.ragnarok/logs"):
        """Export all logs to a zip file for diagnostics"""
        log_dir = os.path.expanduser(log_dir)
        if not os.path.exists(log_dir):
            return False
            
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith('.log') or '.log.' in file:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, os.path.basename(file_path))
            return True
        except Exception:
            return False
