#!/usr/bin/env python3
"""
RagnaRok Framework - API Server Entrypoint
"""

import uvicorn
import argparse
from api.middleware.auth import API_TOKEN

def main():
    parser = argparse.ArgumentParser(description="Start RagnaRok API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind API to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind API to")
    args = parser.parse_args()
    
    print("="*60)
    print("  RagnaRok API Server Starting...")
    print("="*60)
    print(f"  [+] Host: {args.host}")
    print(f"  [+] Port: {args.port}")
    print(f"  [!] API Token: {API_TOKEN}")
    print("  [!] Please use header: X-Api-Token")
    print("="*60)
    
    uvicorn.run("api.app:app", host=args.host, port=args.port, reload=False, access_log=True)

if __name__ == "__main__":
    main()
