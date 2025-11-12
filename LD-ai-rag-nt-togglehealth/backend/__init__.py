"""
ToggleBank RAG System Backend

This package contains the Python backend components for the ToggleBank RAG system,
including the FastAPI web server, terminal chat interface, and user service.
"""

__version__ = "1.0.0"
__author__ = "ToggleBank Team"

# Import main components for easy access
from .fastapi_wrapper import app
from .user_service import UserService, get_user_service
from .script import main

__all__ = ["app", "UserService", "get_user_service", "main"] 