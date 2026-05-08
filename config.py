"""
config.py — Application Configuration
--------------------------------------
Centralizes all configuration settings for the Flask application.
Uses environment variables for production security.

MySQL Connection Configuration:
  - Uses mysql-connector-python as the MySQL driver
  - Connection parameters are loaded from environment variables in production
  - Default values are provided for local development
"""

import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Flask configuration class."""

    # Secret key for session management (uses env variable in production)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-college-event-mgmt-secret-2024')

    # ============================================================
    # MySQL Database Configuration
    # ============================================================
    # In production (Render), these come from environment variables
    # linked to a MySQL cloud service (e.g., Aiven, TiDB, PlanetScale)
    # ============================================================
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'college_events')

    # Session configuration
    SESSION_TYPE = 'filesystem'

    # Debug mode (auto-detected: False on Render, True locally)
    DEBUG = os.environ.get('RENDER') is None
