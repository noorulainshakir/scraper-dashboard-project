"""
Legacy app.py - redirects to new main.py
This file is kept for backward compatibility
"""
import sys
import os

# Redirect to new main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

__all__ = ["app"]
