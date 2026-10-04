# Changelog

All notable changes to the RagnaRok framework will be documented in this file.

## [v1.0.0] - 2026-10-04
### Added
- **REST API (`FastAPI`)**: Full implementation of secure REST API mirroring CLI functionality without overlapping concerns.
- **Role-Based Access Control (RBAC)**: Centralized token-based authentication via `auth_service.py` with Administrator, Analyst, and Viewer roles.
- **Workspace Isolation**: Database-level isolation preventing cross-workspace data access utilizing SQLite `ON DELETE CASCADE` constraints.
- **Reporting Engine**: Dynamic HTML/Markdown/JSON executive reporting using `Jinja2`, scoped tightly to user workspaces.
- **Historical Analysis**: Introduced tracking tables (`scans`, `scan_hosts`, `scan_services`) to capture snapshots of network topologies and allow timeline diffing.
- **Resource Scripts & Global Configuration**: Support for `.rc` files and `config.toml`, handling pre-flight checks and preventing unsafe executions.
- **Data Protection**: Implementation of `cryptography.fernet` protecting session metadata and payload descriptors at rest.
- **Centralized Auditing & Logging**: Standardized Python `logging` mechanisms integrated seamlessly with `AuditLogger`.

### Changed
- **Database Architecture**: Transitioned to `PRAGMA journal_mode=WAL` (Write-Ahead Logging) to permit concurrent SQLite reads/writes, fixing `database is locked` issues.
- **HTTP Beacon Payloads**: Removed arbitrary shell execution (`subprocess.check_output`) from generated payloads to restrict framework to authorized connection/health simulations. 
- **Session Handlers**: Reworked `HTTPHandler` thread management to ensure graceful shutdowns without memory leaks or port exhaustion.

### Security
- Migrated hardcoded secrets to dynamic `.env` configurations using `python-dotenv`.
- Fixed multiple Insecure Direct Object References (IDOR) across REST API endpoints.
- Patched thread exhaustion vulnerabilities within the BaseHTTPRequestHandler loop.

---

## [v0.1.0] - Alpha
- Initial prototype consisting of PySploitFramework and PySploitConsole.
- Basic interactive CLI, raw module implementations, and initial SQLite scaffolding.
