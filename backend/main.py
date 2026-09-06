"""
Backend directory entry point for Render / Uvicorn deployment.
Supports running uvicorn main:app from inside backend folder.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add current backend directory to sys.path
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.main import app
