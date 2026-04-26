"""
config.py — Application Configuration
--------------------------------------
Centralizes all configuration settings for the Flask application.
Uses environment variables for production security.
"""

import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Flask configuration class."""

    # Secret key for session management (uses env variable in production)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-college-event-mgmt-secret-2024')

    # SQLite database path
    DATABASE = os.path.join(BASE_DIR, 'database', 'college_events.db')

    # Session configuration
    SESSION_TYPE = 'filesystem'

    # Debug mode (auto-detected: False on Render, True locally)
    DEBUG = os.environ.get('RENDER') is None
