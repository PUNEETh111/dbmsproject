"""
db.py — Database Connection Helper
-----------------------------------
Provides a centralized database connection manager using SQLite.
Implements connection pooling via Flask's 'g' object and ensures
foreign key enforcement and WAL journal mode for performance.
"""

import sqlite3
from flask import g, current_app


def get_db():
    """
    Get a database connection for the current request.
    Stores the connection in Flask's 'g' object so it is reused
    throughout the request lifecycle.

    Returns:
        sqlite3.Connection: Active database connection with Row factory.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES,
            isolation_level=None  # Manual transaction control (autocommit mode)
        )
        # Return rows as dictionary-like objects
        g.db.row_factory = sqlite3.Row
        # Enable foreign key enforcement (critical for referential integrity)
        g.db.execute("PRAGMA foreign_keys = ON")
        # Use WAL mode for better concurrent read performance
        g.db.execute("PRAGMA journal_mode = WAL")

    return g.db


def close_db(e=None):
    """
    Close the database connection at the end of a request.
    Called automatically by Flask's teardown mechanism.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Initialize the database by executing the schema SQL file.
    Creates all tables, views, and triggers from schema.sql.
    """
    db = get_db()
    with current_app.open_resource('database/schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))


def seed_db():
    """
    Populate the database with sample data from seed.sql.
    """
    db = get_db()
    with current_app.open_resource('database/seed.sql') as f:
        db.executescript(f.read().decode('utf-8'))
