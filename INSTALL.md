# RagnaRok - Installation & Setup Guide

RagnaRok (PySploitFramework/Console) is an authorized security-testing framework that provides isolated workspaces, a REST API, role-based access control, secure reporting, and isolated command and control emulation (HTTP Beacon). 

## Prerequisites
- **OS**: Linux (Kali Linux / Ubuntu recommended)
- **Python**: 3.10 or higher
- **Packages**: `sqlite3`, `pip`, `venv`

## Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/ghassen15874/RagnaRock- RagnaRok
   cd RagnaRok
   ```

2. **Set Up Python Virtual Environment**
   It's highly recommended to run the framework within a virtual environment.
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   Install the required Python modules using pip:
   ```bash
   pip install -r requirements.txt
   ```
   *(Required packages include: fastapi, uvicorn, pydantic, passlib, PyJWT, cryptography, python-dotenv, rich, toml, pytest)*

4. **Initialize Configuration & Environment**
   Generate a secure `.env` file for cryptography keys and JWT secrets. 
   *(The system will automatically generate these and secure them with `0600` permissions on first boot if they are missing).*
   
   If you wish to configure settings manually before boot, use the global configuration file:
   ```bash
   cp core/config.toml.example core/config.toml
   ```

5. **First Boot & Database Migration**
   The database tables and initial user settings are created automatically upon starting the framework or the API.
   - Run the console to initialize:
     ```bash
     python3 ragnarok.py
     ```
   - The default `Administrator` account will be created (Username: `admin`, Password: `admin123`). **Change this password immediately in production.**

## Running the Components

### 1. The Interactive Console (CLI)
Provides an interactive shell to manage workspaces, configure modules, and spin up HTTP Beacons.
```bash
python3 ragnarok.py
```
**Options:**
- `--config <file>`: Load a specific configuration file.
- `--workspace <name>`: Start directly in a specific workspace.
- `--script <file.rc>`: Execute a series of commands sequentially on startup.

### 2. The REST API Server
Provides external integrations, report generation, and full RBAC access to all data.
```bash
python3 start_api.py
# Or run manually via uvicorn:
uvicorn api.app:app --host 127.0.0.1 --port 8000
```
- Access the OpenAPI interactive documentation at: `http://127.0.0.1:8000/docs`.
- The API does not start automatically when you run the CLI. It runs independently to maintain component isolation.

## Security Recommendations
- **Key Rotation**: Rotate your `RAGNAROK_SECRET_KEY` in `.env` periodically. Old sessions will gracefully expire if they cannot be decrypted.
- **Port Exposure**: Do not expose the REST API (port 8000) or HTTP Beacons to untrusted interfaces unless properly segmented.
- **RBAC**: Utilize the Analyst and Viewer roles for team members who do not need Administrator capabilities.
