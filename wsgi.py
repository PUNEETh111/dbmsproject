"""
wsgi.py — Production Entry Point
----------------------------------
Used by Gunicorn on Render to serve the Flask application.
"""

import os
from app import create_app, seed_sample_data
from database.db import get_db, init_db

app = create_app()

# Initialize database on startup (Render creates a fresh instance)
with app.app_context():
    db_path = app.config['DATABASE']
    need_init = False

    if not os.path.exists(db_path):
        need_init = True
    else:
        try:
            db = get_db()
            db.execute("SELECT 1 FROM STUDENT LIMIT 1")
            db.execute("SELECT 1 FROM EVENT LIMIT 1")
        except Exception:
            need_init = True

    if need_init:
        init_db()
        seed_sample_data()
        print('✅ Database created and seeded on Render.')
