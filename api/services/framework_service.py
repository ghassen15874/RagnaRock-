import sys
import os

# Ensure the root path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.framework import PySploitFramework

class FrameworkService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # We initialize framework without starting listeners or interactive shell
            cls._instance = PySploitFramework(quiet=True)
        return cls._instance

    @classmethod
    def get_db(cls):
        return cls.get_instance().session_manager.db
