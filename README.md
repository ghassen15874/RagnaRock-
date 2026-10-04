# RagnaRok (PySploit) Framework

**Version:** 2.0
**Codename:** RagnaRok

RagnaRok is a modular penetration testing framework designed for authorized commercial, laboratory, and controlled environments. It features a complete architecture for discovering vulnerabilities and managing persistent sessions.

## Architecture Overview

*   **`PySploitFramework` (`core/framework.py`)**: The central engine. Automatically discovers and loads all modules dynamically upon startup.
*   **`SessionManager` (`core/session_manager.py`)**: Handles the lifecycle of all active connections. Backed by a thread-safe WAL-mode SQLite database (`sessions.db`).
*   **`HTTPHandler` & `ReverseShellHandler` (`core/handlers.py`)**: Listener infrastructure operating in background threads.
*   **`EvasionEngine` (`core/evasion_engine.py`)**: Processing layer for payload obfuscation.

## Modes of Operation

### A. Console Mode (MSFConsole Style)
The interactive interface for interacting with modules and sessions.
```bash
python3 pysploit.py
```
**Key Commands:**
*   `use <module>`: Select a module.
*   `set <OPTION> <VALUE>`: Configure module parameters.
*   `run` or `exploit`: Execute the current module.
*   `sessions list`: View all active and inactive sessions.
*   `sessions interact <id>`: Drop into an interactive shell.

### B. Venom Mode (MSFVenom Style)
A non-interactive CLI for generating and encoding payloads.
```bash
python3 pysploit.py venom -p <payload> --lhost <IP> --lport <PORT> [-e <encoder>] [-f <format>] [-o <output_file>]
```

## Development & Testing

RagnaRok includes an integration and unit test suite.
To verify framework integrity:
```bash
python3 -m pytest tests/ -v
```
