"""
wsgi.py — Production Entry Point (MySQL Edition)
---------------------------------------------------
Used by Gunicorn on Render to serve the Flask application.
The app module handles MySQL database initialization automatically.
"""

from app import app

# The 'app' object from app.py is already initialized with:
#   1. MySQL database creation (CREATE DATABASE IF NOT EXISTS)
#   2. Schema initialization (CREATE TABLE, VIEW, TRIGGER, INDEX)
#   3. Sample data seeding (INSERT with hashed passwords)
# No additional initialization needed here.
