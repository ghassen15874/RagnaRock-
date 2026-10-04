#!/usr/bin/env python3
"""
RagnaRok Framework – Unit & Integration Tests

Run with:
    cd /home/kali/Desktop/Project/RagnaRok
    python3 -m pytest tests/ -v

Tests cover:
  - Session lifecycle (create, retrieve, close, kill-all, cleanup)
  - Session counter seeding on restart (B2 regression)
  - Duplicate create_session removed (B1 regression)
  - Cleanup DB sync (B10 regression)
  - DB import validation (S3 regression)
  - AES encoder key not in output (S2 regression)
  - Thread-safe scan_port (B4 regression)
  - Auxiliary base get_option safety (B9 regression)
  - Exploit base get_option safety (B7 regression)
  - Module loading and framework init
  - Port scanner parse helpers
"""

import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest

# Ensure the package root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _make_db(path):
    from core.session_db import SessionDatabase
    return SessionDatabase(db_path=path)


def _make_session(sid="test-1", stype="reverse_shell", target="127.0.0.1:9999"):
    from core.session_manager import Session
    s = Session(sid, stype, target)
    return s


# ─────────────────────────────────────────────
#  SessionDatabase tests
# ─────────────────────────────────────────────

class TestSessionDatabase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = _make_db(self.tmp.name)

    def tearDown(self):
        for ext in ('', '-wal', '-shm'):
            try:
                os.unlink(self.tmp.name + ext)
            except FileNotFoundError:
                pass

    def test_save_and_load_session(self):
        s = _make_session("rs-1")
        result = self.db.save_session(s)
        self.assertTrue(result)
        sessions = self.db.load_sessions()
        ids = [x['session_id'] for x in sessions]
        self.assertIn("rs-1", ids)

    def test_deactivate_session(self):
        s = _make_session("rs-2")
        self.db.save_session(s)
        self.db.deactivate_session("rs-2")
        sessions = self.db.load_sessions()
        for sess in sessions:
            if sess['session_id'] == 'rs-2':
                self.assertFalse(sess['active'])

    def test_deactivate_all(self):
        self.db.save_session(_make_session("rs-3"))
        self.db.save_session(_make_session("rs-4"))
        self.db.deactivate_all_sessions()
        for s in self.db.load_sessions():
            self.assertFalse(s['active'])

    def test_load_sessions_empty_db(self):
        sessions = self.db.load_sessions()
        self.assertIsInstance(sessions, list)

    # S3 regression: import validation rejects missing required fields
    def test_import_sessions_rejects_missing_fields(self):
        bad_data = {"export_time": "2026-01-01T00:00:00", "sessions": [{"session_id": "x-1"}]}
        export_file = self.tmp.name + ".import.json"
        with open(export_file, 'w') as f:
            json.dump(bad_data, f)
        try:
            result = self.db.import_sessions(export_file)
            self.assertTrue(result)
            ids = [x['session_id'] for x in self.db.load_sessions()]
            self.assertNotIn("x-1", ids)
        finally:
            try: os.unlink(export_file)
            except FileNotFoundError: pass

    def test_import_sessions_rejects_invalid_json(self):
        bad_file = self.tmp.name + ".bad.json"
        with open(bad_file, 'w') as f:
            f.write("NOT JSON")
        try:
            self.assertFalse(self.db.import_sessions(bad_file))
        finally:
            try: os.unlink(bad_file)
            except FileNotFoundError: pass

    def test_import_sessions_rejects_non_object(self):
        bad_file = self.tmp.name + ".arr.json"
        with open(bad_file, 'w') as f:
            json.dump([1, 2, 3], f)
        try:
            self.assertFalse(self.db.import_sessions(bad_file))
        finally:
            try: os.unlink(bad_file)
            except FileNotFoundError: pass

    def test_import_valid_sessions(self):
        good_data = {"export_time": "2026-01-01T00:00:00", "sessions": [{
            "session_id": "imported-1", "type": "reverse_shell", "target": "10.0.0.1:1234",
            "created_at": "2026-01-01T00:00:00", "last_seen": "2026-01-01T00:01:00",
            "active": True, "metadata": {}
        }]}
        export_file = self.tmp.name + ".good.json"
        with open(export_file, 'w') as f:
            json.dump(good_data, f)
        try:
            self.assertTrue(self.db.import_sessions(export_file))
            ids = [x['session_id'] for x in self.db.load_sessions()]
            self.assertIn("imported-1", ids)
        finally:
            try: os.unlink(export_file)
            except FileNotFoundError: pass

    def test_wal_mode_enabled(self):
        with sqlite3.connect(self.tmp.name) as conn:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        self.assertEqual(mode, 'wal')

    def test_database_stats(self):
        self.db.save_session(_make_session("rs-stat"))
        stats = self.db.get_database_stats()
        self.assertIn('total_sessions', stats)
        self.assertGreaterEqual(stats['total_sessions'], 1)


# ─────────────────────────────────────────────
#  SessionManager tests
# ─────────────────────────────────────────────

class TestSessionManager(unittest.TestCase):

    def _patch_db(self, tmp_path):
        from core import session_db
        orig = session_db.SessionDatabase.__init__
        def patched(self_db, db_path="sessions.db"):
            orig(self_db, db_path=tmp_path)
        session_db.SessionDatabase.__init__ = patched
        return orig

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self._orig = self._patch_db(self.tmp.name)
        from core.session_manager import SessionManager
        self.sm = SessionManager()

    def tearDown(self):
        from core import session_db
        session_db.SessionDatabase.__init__ = self._orig
        for ext in ('', '-wal', '-shm'):
            try: os.unlink(self.tmp.name + ext)
            except FileNotFoundError: pass

    def test_create_returns_id(self):
        sid = self.sm.create_session("test_shell", "127.0.0.1:9999")
        self.assertIsInstance(sid, str)
        self.assertTrue(sid.startswith("test_shell-"))

    def test_get_session(self):
        sid = self.sm.create_session("test_shell", "127.0.0.1:9999")
        session = self.sm.get_session(sid)
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, sid)

    def test_list_sessions(self):
        self.sm.create_session("test_shell", "10.0.0.1:1")
        self.sm.create_session("test_shell", "10.0.0.1:2")
        self.assertGreaterEqual(len(self.sm.list_sessions()), 2)

    def test_close_session(self):
        sid = self.sm.create_session("test_shell", "127.0.0.1:9999")
        self.assertTrue(self.sm.close_session(sid))
        self.assertIsNone(self.sm.get_session(sid))

    def test_close_nonexistent_session(self):
        self.assertFalse(self.sm.close_session("does-not-exist-999"))

    def test_kill_all_sessions(self):
        self.sm.create_session("test_shell", "10.0.0.1:1")
        self.sm.create_session("test_shell", "10.0.0.1:2")
        count = self.sm.kill_all_sessions()
        self.assertGreaterEqual(count, 2)
        self.assertEqual(len(self.sm.sessions), 0)

    # B2 regression: counter must increment
    def test_counter_increments(self):
        sid1 = self.sm.create_session("x", "a")
        sid2 = self.sm.create_session("x", "b")
        n1 = int(sid1.rsplit("-", 1)[1])
        n2 = int(sid2.rsplit("-", 1)[1])
        self.assertGreater(n2, n1)

    # B1 regression: create_session defined exactly once
    def test_no_duplicate_create_session(self):
        from core.session_manager import SessionManager
        import inspect
        src = inspect.getsource(SessionManager)
        count = src.count("def create_session")
        self.assertEqual(count, 1, "create_session must be defined exactly once")

    # B10 regression: cleanup syncs DB
    def test_cleanup_deactivates_in_db(self):
        sid = self.sm.create_session("test_shell", "127.0.0.1:9999")
        self.sm.get_session(sid).active = False
        self.sm.cleanup_sessions()
        rows = self.sm.db.load_sessions()
        for row in rows:
            if row['session_id'] == sid:
                self.assertFalse(row['active'])

    def test_get_session_stats(self):
        self.sm.create_session("test_shell", "10.0.0.1:1")
        stats = self.sm.get_session_stats()
        self.assertIn('total', stats)

    def test_concurrent_session_creation(self):
        results = []
        lock = threading.Lock()

        def create():
            sid = self.sm.create_session("concurrent", "127.0.0.1")
            with lock:
                results.append(sid)

        threads = [threading.Thread(target=create) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(len(results), 10)
        self.assertEqual(len(set(results)), 10, "All session IDs must be unique")


# ─────────────────────────────────────────────
#  AuxiliaryBase tests
# ─────────────────────────────────────────────

class TestAuxiliaryBase(unittest.TestCase):

    def setUp(self):
        from auxiliary.auxiliary_base import AuxiliaryBase
        self.base = AuxiliaryBase()
        self.base.options = {
            'RHOSTS': {'type': 'string', 'required': True, 'description': 'Target'},
            'THREADS': {'type': 'int', 'default': 50, 'description': 'Thread count'},
        }

    # B9 regression: unknown option must not raise KeyError
    def test_get_option_unknown_key(self):
        self.assertIsNone(self.base.get_option('NONEXISTENT'))

    def test_get_option_default(self):
        self.assertEqual(self.base.get_option('THREADS'), 50)

    def test_get_option_set_value(self):
        self.base.options['THREADS']['value'] = 100
        self.assertEqual(self.base.get_option('THREADS'), 100)

    def test_framework_attr_initialized(self):
        from auxiliary.auxiliary_base import AuxiliaryBase
        self.assertIsNone(AuxiliaryBase().framework)

    def test_run_raises_not_implemented(self):
        from auxiliary.auxiliary_base import AuxiliaryBase
        with self.assertRaises(NotImplementedError):
            AuxiliaryBase().run()


# ─────────────────────────────────────────────
#  Exploit base tests
# ─────────────────────────────────────────────

class TestExploitBase(unittest.TestCase):

    def setUp(self):
        from exploits.base import Exploit
        self.exploit = Exploit()
        self.exploit.options = {
            'RHOST': {'type': 'string', 'required': True, 'description': 'Target IP'},
            'RPORT': {'type': 'int', 'default': 21, 'description': 'Target port'},
        }

    # B7 regression: get_option with default, no KeyError
    def test_get_option_with_default(self):
        self.assertEqual(self.exploit.get_option('RPORT'), 21)

    def test_get_option_unknown_key(self):
        self.assertIsNone(self.exploit.get_option('NONEXISTENT'))

    def test_get_option_set_value(self):
        self.exploit.options['RHOST']['value'] = '192.168.1.100'
        self.assertEqual(self.exploit.get_option('RHOST'), '192.168.1.100')

    def test_check_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.exploit.check("127.0.0.1")

    def test_exploit_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.exploit.exploit("127.0.0.1", None)


# ─────────────────────────────────────────────
#  AES Encoder tests
# ─────────────────────────────────────────────

class TestAESEncoder(unittest.TestCase):

    def setUp(self):
        from encoders.aes import AESEncoder
        self.encoder = AESEncoder()

    # S2 regression: encryption key must NOT appear in output
    def test_key_not_in_output(self):
        output = self.encoder.encode("test payload")
        self.assertNotIn("'key'", output, "Encryption key must not appear in encoder output (S2)")

    def test_output_contains_ciphertext(self):
        self.assertIn("ciphertext", self.encoder.encode("test payload"))

    def test_output_contains_salt(self):
        self.assertIn("salt", self.encoder.encode("test payload"))

    def test_encode_bytes_input(self):
        self.assertIn("ciphertext", self.encoder.encode(b"binary payload"))


# ─────────────────────────────────────────────
#  Port Scanner tests
# ─────────────────────────────────────────────

class TestPortScanner(unittest.TestCase):

    def setUp(self):
        from auxiliary.scanner import PortScanner
        self.scanner = PortScanner()

    def test_parse_single_port(self):
        self.assertEqual(self.scanner.parse_ports("80"), [80])

    def test_parse_port_range(self):
        self.assertEqual(self.scanner.parse_ports("80-82"), [80, 81, 82])

    def test_parse_mixed_ports(self):
        ports = self.scanner.parse_ports("22,80-81,443")
        self.assertIn(22, ports)
        self.assertIn(80, ports)
        self.assertIn(81, ports)
        self.assertIn(443, ports)

    def test_parse_single_host(self):
        self.assertEqual(self.scanner.parse_hosts("192.168.1.1"), ["192.168.1.1"])

    def test_parse_host_range(self):
        hosts = self.scanner.parse_hosts("192.168.1.1-3")
        self.assertIn("192.168.1.1", hosts)
        self.assertIn("192.168.1.3", hosts)

    def test_get_service_name_known(self):
        self.assertEqual(self.scanner.get_service_name(22), "SSH")
        self.assertEqual(self.scanner.get_service_name(80), "HTTP")

    def test_get_service_name_unknown(self):
        self.assertEqual(self.scanner.get_service_name(12345), "Unknown")

    # B4 regression: thread-safe counter update
    def test_scan_port_thread_safety(self):
        import concurrent.futures
        self.scanner.open_ports = []
        self.scanner.scanned_count = 0
        ports = list(range(60000, 60020))
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futs = [ex.submit(self.scanner.scan_port, "127.0.0.1", p, 0.1, False) for p in ports]
            [f.result() for f in futs]
        self.assertEqual(self.scanner.scanned_count, 20)


# ─────────────────────────────────────────────
#  Framework loading tests (integration)
# ─────────────────────────────────────────────

class TestFrameworkLoad(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.tmp.close()
        from core import session_db
        cls._orig = session_db.SessionDatabase.__init__
        tmp_path = cls.tmp.name
        def patched(self_db, db_path="sessions.db"):
            cls._orig(self_db, db_path=tmp_path)
        session_db.SessionDatabase.__init__ = patched
        from core.framework import PySploitFramework
        cls.framework = PySploitFramework()

    @classmethod
    def tearDownClass(cls):
        from core import session_db
        session_db.SessionDatabase.__init__ = cls._orig
        for ext in ('', '-wal', '-shm'):
            try: os.unlink(cls.tmp.name + ext)
            except FileNotFoundError: pass

    def test_exploits_loaded(self):
        self.assertGreater(len(self.framework.exploits), 0)

    def test_auxiliary_loaded(self):
        self.assertGreater(len(self.framework.auxiliary), 0)

    def test_encoders_loaded(self):
        self.assertGreater(len(self.framework.encoders), 0)

    def test_formatters_loaded(self):
        self.assertGreater(len(self.framework.formatters), 0)

    def test_session_manager_exists(self):
        self.assertIsNotNone(self.framework.session_manager)

    def test_vsftpd_loaded(self):
        self.assertIn('vsftpd_234', self.framework.exploits)

    def test_portscan_loaded(self):
        self.assertIn('portscan', self.framework.auxiliary)

    def test_exploits_have_framework_ref(self):
        for name, exploit in self.framework.exploits.items():
            self.assertIsNotNone(exploit.framework, f"Exploit {name} has no framework reference")

    def test_no_dead_load_exploits_method(self):
        """Regression: the dead load_exploits() method must not exist."""
        self.assertFalse(
            hasattr(self.framework, 'load_exploits'),
            "Dead load_exploits() method should have been removed (B3)"
        )


# ─────────────────────────────────────────────
#  ModuleManager tests
# ─────────────────────────────────────────────

class TestModuleManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.tmp.close()
        from core import session_db
        cls._orig = session_db.SessionDatabase.__init__
        tmp_path = cls.tmp.name
        def patched(self_db, db_path="sessions.db"):
            cls._orig(self_db, db_path=tmp_path)
        session_db.SessionDatabase.__init__ = patched
        from core.framework import PySploitFramework
        from core.module_manager import ModuleManager
        cls.framework = PySploitFramework()
        cls.mm = ModuleManager(cls.framework)

    @classmethod
    def tearDownClass(cls):
        from core import session_db
        session_db.SessionDatabase.__init__ = cls._orig
        for ext in ('', '-wal', '-shm'):
            try: os.unlink(cls.tmp.name + ext)
            except FileNotFoundError: pass

    def test_use_exploit_full_path(self):
        success, _ = self.mm.use("exploit/vsftpd_234")
        self.assertTrue(success)
        self.assertEqual(self.mm.module_type, 'exploit')

    def test_use_exploit_short_name(self):
        success, _ = self.mm.use("vsftpd_234")
        self.assertTrue(success)

    def test_use_auxiliary(self):
        success, _ = self.mm.use("auxiliary/portscan")
        self.assertTrue(success)
        self.assertEqual(self.mm.module_type, 'auxiliary')

    def test_use_unknown_module(self):
        success, _ = self.mm.use("exploit/does_not_exist")
        self.assertFalse(success)

    def test_set_option(self):
        self.mm.use("exploit/vsftpd_234")
        ok, _ = self.mm.set_option("RHOST", "192.168.1.100")
        self.assertTrue(ok)
        self.assertEqual(self.mm._get_option_value("RHOST"), "192.168.1.100")

    def test_back_clears_module(self):
        self.mm.use("exploit/vsftpd_234")
        self.mm.back()
        self.assertIsNone(self.mm.current_module)

    def test_discover_options_no_module(self):
        self.mm.back()
        self.assertIn("No module", self.mm.discover_options())

    def test_prompt_with_module(self):
        self.mm.use("exploit/vsftpd_234")
        self.assertIn("exploit", self.mm.get_prompt())

    def test_prompt_without_module(self):
        self.mm.back()
        self.assertEqual(self.mm.get_prompt(), "pysploit")


if __name__ == '__main__':
    unittest.main(verbosity=2)
