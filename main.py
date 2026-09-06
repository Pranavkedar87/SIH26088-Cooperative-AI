"""
Root entry point for Render / Uvicorn deployment.
Supports running uvicorn main:app from root repository folder.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path so app module is discoverable
_backend_dir = Path(__file__).resolve().parent / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.main import app
