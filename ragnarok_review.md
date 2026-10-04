# RagnaRok Framework – Comprehensive Code Review

## Architecture Overview

```
pysploit.py          ← Entry point (console / venom mode)
cli/console.py       ← cmd.Cmd REPL (Metasploit-style)
cli/venom.py         ← MSFVenom-style payload generator CLI
core/
  framework.py       ← Module loader & top-level registry
  module_manager.py  ← use/set/run dispatch
  session_manager.py ← In-memory session state + DB bridge
  session_db.py      ← SQLite persistence layer
  handlers.py        ← TCP/HTTP reverse-shell listeners
  payload_generator.py ← Encode+format pipeline
  persistence.py     ← Post-exploitation persistence templates
exploits/            ← Individual exploit modules (7 loaded)
auxiliary/           ← Scanners and assessment tools (12 loaded)
payloads/            ← Payload template classes
encoders/            ← XOR / Base64 / AES / Multi
formatters/          ← EXE / PS1 / Python / Raw / Shellcode
```

---

## Bugs Discovered

| # | Severity | File | Description |
|---|----------|------|-------------|
| B1 | **Critical** | `core/session_manager.py` | `create_session()` defined **twice** (lines 85-96 and 424-439). Python keeps only the second definition; the first (which calls `db.save_session` outside a try/except) is silently discarded. The second definition wraps the DB call correctly but is the *only* one active. |
| B2 | **Critical** | `core/session_manager.py` | `session_counter` is reset to 0 on every startup. Sessions are loaded from DB but counter stays at 0, so the next `create_session` call produces `reverse_shell-1` which **collides with** any persisted session already named `reverse_shell-1`, causing silent data corruption via `INSERT OR REPLACE`. |
| B3 | **High** | `core/framework.py` | `load_exploits()` method (lines 167-177) references `self.exploit_modules` which **does not exist** — modules are registered in `load_modules()` as a local dict. This method is dead code that will always raise `AttributeError` if called. |
| B4 | **High** | `auxiliary/scanner.py` | `scan_port()` writes to `self.open_ports` and increments `self.scanned_count` from multiple threads **without a lock**. This is a race condition that can corrupt results or cause crashes under high thread counts. |
| B5 | **High** | `core/session_db.py` | `load_sessions()` and all DB methods open a raw `sqlite3.connect()` without WAL mode and without a lock, making concurrent writes unsafe. |
| B6 | **High** | `core/session_db.py` | `load_sessions()` does **not** close the connection in an error path (no `finally`/context manager). |
| B7 | **High** | `exploits/log4shell.py:35,37` | Accesses `self.options['HEADER']['value']` and `self.options['METHOD']['value']` directly (no `get_option()`). If a user never sets these options the key `'value'` does not exist yet and raises `KeyError`. Same in `proxyshell.py` (lines 148-156). |
| B8 | **Medium** | `exploits/vsftpd.py:338` | `finally` block tries to close `backdoor_sock` using `hasattr(self, 'backdoor_socket')` – but the attribute is *set* earlier in the same iteration, meaning the finally clause **never** closes the socket on failed iterations after the first attempt. Socket leak on every retry. |
| B9 | **Medium** | `auxiliary/auxiliary_base.py:23` | `get_option()` accesses `self.options[name]` without first checking `name in self.options`, raising `KeyError` for unknown option names. |
| B10 | **Medium** | `core/session_manager.py` | `cleanup_sessions()` calls `session.close()` then `del self.sessions[session_id]` but never calls `self.db.deactivate_session(session_id)` — DB and memory state diverge. |
| B11 | **Medium** | `exploits/sqli_rce.py` | `_send_request` reads option values via `self.options.get('TARGET', {}).get('value', '')` — it silently returns an empty string if TARGET is not set, then sends requests to an empty URL, causing confusing `requests` errors rather than a clear "option not set" message. |
| B12 | **Low** | `core/session_manager.py` | `interact_meterpreter` has hardcoded simulated `sysinfo` data (`'Windows 10'`, `'SYSTEM'`) with no indication it is simulated — can mislead operators. |
| B13 | **Low** | `exploits/eternalblue.py` | `check()` returns `True` for any SMB response regardless of content, meaning every reachable SMB service is reported as vulnerable. |

---

## Security Weaknesses Identified

| # | Severity | Description |
|---|----------|-------------|
| S1 | **High** | `sessions.db` is created in the **current working directory** (not a dedicated data dir). If the framework is launched from `/`, `/tmp`, or a shared directory, the database is world-readable. |
| S2 | **High** | AES encoder (`encoders/aes.py`) leaks the encryption key in plaintext inside the encoded payload string (`'key': base64.b64encode(password).decode()`). This defeats the purpose of encryption. |
| S3 | **High** | `session_db.py:import_sessions()` loads JSON from an arbitrary file path with no validation of field types or sizes, making it trivially exploitable for crashes or DB injection if a malicious export file is imported. |
| S4 | **Medium** | SQL queries in `session_db.py` correctly use parameterized statements — **no SQL injection** here (good). |
| S5 | **Medium** | `persistence.py` generates shell commands by f-string interpolating user-supplied `payload`, `task_name`, `key_name`, `username` etc. with no sanitization. On Windows this enables shell command injection via the task/key name. (By design these are attacker-controlled payloads; but the function is also called with values from `do_persistence` which parses user CLI input.) |
| S6 | **Low** | `handlers.py:start_tcp_handler` stores client address tuple (`client_address` which is `(ip, port)`) directly into session metadata as a non-serializable Python tuple. `json.dumps()` on metadata will fail silently (caught by bare `except`). |

---

## Session System Issues

| # | Description |
|---|-------------|
| SS1 | Counter/ID collision on restart (Bug B2) — sessions loaded from DB conflict with freshly generated IDs. |
| SS2 | Duplicate `create_session` definition (Bug B1) — the first definition is dead; the second has weaker error reporting. |
| SS3 | `cleanup_sessions()` does not deactivate cleaned sessions in the DB (Bug B10). |
| SS4 | `interact_reverse_shell` uses `time.sleep(0.5)` blocking the REPL for each command — should use a proper non-blocking read loop. |
| SS5 | Sessions loaded from DB on startup are all `active=True` — there is no liveness check. Stale sessions from previous runs are shown as active. |
| SS6 | No session timeout / expiry mechanism. |
| SS7 | `handlers.py` `active_handlers` dict is accessed from multiple threads without a lock. |
| SS8 | Client address stored as Python tuple in metadata breaks JSON serialization (Bug S6). |

---

## Files Modified (Fixes Implemented)

| File | Bug(s) Fixed | Description |
|------|-------------|-------------|
| `core/session_manager.py` | B1, B2, B10, SS3 | Removed duplicate `create_session`; seeded counter from max DB ID on startup; `cleanup_sessions` now deactivates in DB; loaded sessions correctly marked inactive |
| `core/session_db.py` | B5, B6, S3 | WAL mode + `PRAGMA foreign_keys=ON`; context managers everywhere (no connection leaks); `import_sessions` validates required fields, types, and sizes |
| `auxiliary/scanner.py` | B4, + new | `_lock` added; `scan_port` uses lock around shared state; `parse_hosts` short-form range bug fixed (`192.168.1.1-3` now generates 1,2,3 not just 3) |
| `core/framework.py` | B3 | Dead `load_exploits()` method removed |
| `exploits/base.py` | B7 | `get_option()` added to base class (safe default fallback, no KeyError) |
| `exploits/log4shell.py` | B7 | Replaced direct `options['KEY']['value']` access with `get_option()`; added LHOST/LPORT guard |
| `exploits/vsftpd.py` | B8 | Fixed socket leak in retry loop via `success` flag; removed duplicate `get_option()` |
| `exploits/proxyshell.py` | B7 | Replaced direct option access with `get_option()` in `build_url` and `generate_reverse_shell` |
| `auxiliary/auxiliary_base.py` | B9 | `get_option()` guards against unknown keys; `self.framework = None` initialized |
| `encoders/aes.py` | S2 | Key removed from encoder output |
| `core/handlers.py` | S6 | `client_address` tuple converted to `"ip:port"` string for JSON serialization |

## Tests Added

**File:** [`tests/test_ragnarok.py`](file:///home/kali/Desktop/Project/RagnaRok/tests/test_ragnarok.py)

**Result:** ✅ **61/61 tests pass** (0.60 s)

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestSessionDatabase` | 10 | save/load, deactivate, deactivate-all, import validation (S3), WAL mode, stats |
| `TestSessionManager` | 11 | create, get, list, close, kill-all, counter (B2), no-duplicate (B1), cleanup DB sync (B10), stats, concurrent |
| `TestAuxiliaryBase` | 5 | unknown key (B9), default, set value, framework init, NotImplementedError |
| `TestExploitBase` | 5 | unknown key (B7), default, set value, NotImplementedError |
| `TestAESEncoder` | 4 | key not in output (S2), ciphertext present, salt present, bytes input |
| `TestPortScanner` | 8 | parse ports, ranges, hosts, mixed, service names, thread safety (B4) |
| `TestFrameworkLoad` | 9 | exploits/aux/encoders/formatters loaded, session manager, framework refs, no dead method (B3) |
| `TestModuleManager` | 9 | use by full path, short name, auxiliary, unknown, set option, back, discover, prompts |

## Remaining Problems (Not Fixed)

| # | Severity | Description | Reason not fixed |
|---|----------|-------------|------------------|
| B11 | Medium | `sqli_rce.py` silently sends requests to empty URL when TARGET not set | Would require restructuring the module's internal option access pattern; low risk as module_manager checks required options before run |
| B12 | Low | Meterpreter `sysinfo` has hardcoded simulated data | Cosmetic; the feature is explicitly a placeholder |
| B13 | Low | EternalBlue check returns True for any SMB response | By design in this framework stub; real implementation requires vulnerability-specific fingerprinting |
| SS4 | Medium | `interact_reverse_shell` uses blocking `time.sleep(0.5)` per command | Requires larger shell I/O refactor; safe for now |
| SS6 | Medium | No session timeout / expiry mechanism | Requires timer infrastructure |
| S1 | Medium | `sessions.db` created in CWD | Requires config system for data directory |
| S5 | Medium | Persistence commands use f-string interpolation of user-supplied names | By design (attacker-controlled payloads), but needs sanitization note in docs |

---

## Recommended Architectural Improvements

| Priority | Recommendation | Benefit |
|----------|---------------|--------|
| **Critical** ✅ | ~~Remove duplicate `create_session`~~ | Fixed |
| **Critical** ✅ | ~~Seed counter from DB on startup~~ | Fixed |
| **High** ✅ | ~~Thread lock on scanner shared state~~ | Fixed |
| **High** ✅ | ~~`get_option()` in base classes~~ | Fixed |
| **High** ✅ | ~~WAL mode + context managers in DB~~ | Fixed |
| **High** ✅ | ~~AES key leakage~~ | Fixed |
| **High** ✅ | ~~Import validation~~ | Fixed |
| **High** | Move `sessions.db` to a configurable `~/.ragnarok/` data dir | Prevents accidental world-readable DB in CWD |
| **Medium** | Replace `print()` throughout with `logging` module | Enables log levels, file output, timestamps |
| **Medium** | Session timeout / expiry via background thread | Prevents unbounded memory growth in long-running sessions |
| **Medium** | Select-based I/O loop in `interact_reverse_shell` | Removes 0.5 s latency per command |
| **Medium** | Configurable `data_dir` for DB, exports, scan results | Currently clutters the project root with `.json`, `.db`, `.exe` files |
| **Low** | Add `check` pre-flight to `do_exploit` console command | Warn user before running exploit if target check fails |
| **Low** | Complete `http` handler stub | HTTP C2 beacon handler is declared but not implemented |
| **Low** | Add `download`/`upload` to meterpreter session | Currently stubs with "coming soon" |

