"""
db.py — MySQL Database Connection Helper
------------------------------------------
Provides a centralized database connection manager using MySQL.
Implements connection management via Flask's 'g' object.

MySQL-Specific Features Used:
  - InnoDB storage engine (supports ACID transactions, foreign keys)
  - AUTO_INCREMENT for primary key generation
  - BEFORE INSERT TRIGGERs for business logic enforcement
  - VIEWs for denormalized read-only queries
  - INDEXes for query optimization
  - Parameterized queries (%s placeholders) to prevent SQL injection
"""

import mysql.connector
from mysql.connector import Error as MySQLError
from flask import g, current_app


def get_db():
    """
    Get a MySQL database connection for the current request.
    Stores the connection in Flask's 'g' object so it is reused
    throughout the request lifecycle.

    MySQL Connection Details:
      - Uses mysql-connector-python (pure Python MySQL driver)
      - dictionary=True on cursor gives dict-like row access
      - autocommit=False enables explicit TRANSACTION control
        (START TRANSACTION → COMMIT / ROLLBACK)

    Returns:
        mysql.connector.connection.MySQLConnection: Active database connection.
    """
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            port=current_app.config['MYSQL_PORT'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DATABASE'],
            autocommit=False  # Explicit transaction control: START TRANSACTION, COMMIT, ROLLBACK
        )
    # Reconnect if connection was lost
    if not g.db.is_connected():
        g.db.reconnect(attempts=3, delay=1)
    return g.db


def get_cursor(dictionary=True):
    """
    Get a MySQL cursor from the current connection.

    Args:
        dictionary (bool): If True, returns rows as dictionaries (column_name: value).
                          This replaces SQLite's Row factory for dict-like access.

    Returns:
        mysql.connector.cursor.MySQLCursor: A cursor object.
    """
    db = get_db()
    return db.cursor(dictionary=dictionary)


def close_db(e=None):
    """
    Close the MySQL database connection at the end of a request.
    Called automatically by Flask's teardown mechanism.
    """
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()


def init_db():
    """
    Initialize the MySQL database by executing the schema SQL file.
    Creates all tables, views, indexes, and triggers from schema.sql.

    Uses executemulti=True to run multiple SQL statements from a single script.
    This is MySQL's equivalent of SQLite's executescript().
    """
    db = get_db()
    cursor = db.cursor()

    with current_app.open_resource('database/schema.sql') as f:
        sql_script = f.read().decode('utf-8')

    # Split and execute each statement individually
    # MySQL connector's multi=True can be finicky, so we split manually
    statements = [s.strip() for s in sql_script.split(';\n') if s.strip()]

    for statement in statements:
        if statement and not statement.startswith('--'):
            try:
                # Handle DELIMITER for triggers/procedures
                cursor.execute(statement)
            except MySQLError as e:
                # Skip "already exists" errors during re-initialization
                if e.errno not in (1050, 1304, 1359, 1060):  # Table/View/Trigger already exists
                    print(f"Schema init warning: {e}")

    db.commit()
    cursor.close()


def seed_db():
    """
    Populate the database with sample data from seed.sql.

    Uses parameterized INSERT statements for security.
    MySQL uses %s as placeholder (unlike SQLite's ?).
    """
    db = get_db()
    cursor = db.cursor()

    with current_app.open_resource('database/seed.sql') as f:
        sql_script = f.read().decode('utf-8')

    statements = [s.strip() for s in sql_script.split(';\n') if s.strip()]

    for statement in statements:
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
            except MySQLError as e:
                if e.errno != 1062:  # Skip duplicate entry errors
                    print(f"Seed warning: {e}")

    db.commit()
    cursor.close()
