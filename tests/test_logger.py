import unittest
import os
import tempfile
import threading
from core.logger import LoggerFactory

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        LoggerFactory.setup(log_dir=self.temp_dir.name)
        self.sys_logger = LoggerFactory.get_logger("system")
        
    def tearDown(self):
        LoggerFactory.reset()
        self.temp_dir.cleanup()

    def test_secret_scrubbing(self):
        LoggerFactory.set_trace_id("TEST1")
        self.sys_logger.info("Connecting with password=supersecret123 to DB")
        self.sys_logger.info("API key: token=abcdef123456")
        
        # Read log file
        log_path = os.path.join(self.temp_dir.name, "system.log")
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertNotIn("supersecret123", content)
        self.assertNotIn("abcdef123456", content)
        self.assertIn("password=***MASKED***", content)
        self.assertIn("token=***MASKED***", content)

    def test_log_rotation(self):
        # Reduce maxBytes for testing rotation
        handler = self.sys_logger.handlers[0]
        handler.maxBytes = 100  # Very small size to trigger rotation quickly
        
        for i in range(20):
            self.sys_logger.info(f"This is a relatively long log message to trigger rotation {i}")
            
        # Check files in directory
        files = os.listdir(self.temp_dir.name)
        system_logs = [f for f in files if f.startswith("system.log")]
        
        # Should have system.log, system.log.1, etc.
        self.assertTrue(len(system_logs) > 1, f"Log rotation failed, found: {system_logs}")

    def test_concurrent_logging(self):
        LoggerFactory.set_trace_id("MAIN")
        
        def log_worker(worker_id):
            LoggerFactory.set_trace_id(f"W-{worker_id}")
            for i in range(10):
                self.sys_logger.info(f"Worker {worker_id} logging step {i}")
                
        threads = []
        for i in range(5):
            t = threading.Thread(target=log_worker, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        log_path = os.path.join(self.temp_dir.name, "system.log")
        with open(log_path, 'r') as f:
            content = f.read()
            
        # Ensure all trace IDs are present and not tangled
        for i in range(5):
            self.assertIn(f"[W-{i}]", content)

if __name__ == '__main__':
    unittest.main()
