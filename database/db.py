"""
db.py — Database Connection Helper (MySQL with SQLite Fallback)
-----------------------------------------------------------------
Provides a centralized database connection manager.

Primary Database: MySQL (InnoDB)
  - Full-featured RDBMS with client-server architecture
  - ACID-compliant transactions via InnoDB storage engine
  - Native FOREIGN KEY constraints
  - TRIGGER, VIEW, and INDEX support

Fallback Database: SQLite
  - Used when MySQL environment variables are not configured
  - Enables zero-configuration deployment on platforms like Render
  - All SQL queries are designed to work with both MySQL and SQLite

MySQL-Specific Features Used:
  - InnoDB storage engine (supports ACID transactions, foreign keys)
  - AUTO_INCREMENT for primary key generation
  - BEFORE INSERT TRIGGERs for business logic enforcement
  - VIEWs for denormalized read-only queries
  - INDEXes for query optimization
  - Parameterized queries (%s placeholders) to prevent SQL injection
"""

import os
import sqlite3

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

from flask import g, current_app


def is_mysql_configured():
    """
    Check if MySQL environment variables are properly configured.
    Returns True if MYSQL_HOST is set to a non-localhost value
    (indicating a cloud MySQL instance).
    """
    host = current_app.config.get('MYSQL_HOST', 'localhost')
    password = current_app.config.get('MYSQL_PASSWORD', '')
    return MYSQL_AVAILABLE and host != 'localhost' and password != ''


def _create_sqlite_connection():
    """Create and configure a SQLite connection (used as fallback)."""
    db_path = current_app.config.get('SQLITE_DATABASE',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'college_events.db'))
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_db():
    """
    Get a database connection for the current request.
    Stores the connection in Flask's 'g' object so it is reused
    throughout the request lifecycle.

    If MySQL is configured (via environment variables):
      - Uses mysql.connector.connect() for MySQL connections
      - dictionary=True on cursor gives dict-like row access
      - autocommit=False enables explicit TRANSACTION control

    If MySQL is NOT configured (fallback):
      - Uses sqlite3.connect() with Row factory
      - Provides dict-like access via sqlite3.Row
      - PRAGMA foreign_keys = ON for referential integrity

    Returns:
        Connection object (MySQL or SQLite)
    """
    if 'db' not in g:
        if is_mysql_configured():
            # --- Try MySQL Connection ---
            try:
                conn_params = {
                    'host': current_app.config['MYSQL_HOST'],
                    'port': current_app.config['MYSQL_PORT'],
                    'user': current_app.config['MYSQL_USER'],
                    'password': current_app.config['MYSQL_PASSWORD'],
                    'database': current_app.config['MYSQL_DATABASE'],
                    'autocommit': False,
                    'connection_timeout': 5
                }

                # Enable SSL for cloud MySQL providers (e.g., Aiven, TiDB, PlanetScale)
                if current_app.config.get('MYSQL_SSL', False):
                    conn_params['ssl_disabled'] = False
                    conn_params['ssl_verify_cert'] = False

                g.db = mysql.connector.connect(**conn_params)
                g.db_type = 'mysql'
            except Exception as e:
                # MySQL connection failed — fall back to SQLite
                print(f'⚠️  MySQL connection failed ({e}), using SQLite fallback.')
                g.db = _create_sqlite_connection()
                g.db_type = 'sqlite'
        else:
            # --- SQLite Fallback (no MySQL configured) ---
            g.db = _create_sqlite_connection()
            g.db_type = 'sqlite'

    # Reconnect if MySQL connection was lost
    if g.get('db_type') == 'mysql' and not g.db.is_connected():
        g.db.reconnect(attempts=3, delay=1)

    return g.db


def get_db_type():
    """Return the current database type ('mysql' or 'sqlite')."""
    get_db()  # Ensure connection is established
    return g.get('db_type', 'sqlite')


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a SQL query with automatic MySQL/SQLite compatibility.

    This helper handles the differences between MySQL and SQLite:
      - MySQL uses %s for parameter placeholders
      - SQLite uses ? for parameter placeholders
      - MySQL requires cursor management (create, execute, close)
      - SQLite allows direct db.execute()

    Args:
        query (str): SQL query (use %s for parameters — auto-converted for SQLite)
        params (tuple): Query parameters
        fetch_one (bool): Return single row
        fetch_all (bool): Return all rows
        commit (bool): Commit after execution

    Returns:
        Result based on fetch options, or cursor/lastrowid info dict
    """
    db = get_db()
    db_type = get_db_type()

    if db_type == 'sqlite':
        # Convert MySQL %s placeholders to SQLite ? placeholders
        query = query.replace('%s', '?')
        cursor = db.execute(query, params or ())
        if commit:
            db.commit()
        if fetch_one:
            row = cursor.fetchone()
            # Convert sqlite3.Row to dict for consistent access
            return dict(row) if row else None
        if fetch_all:
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        return {'lastrowid': cursor.lastrowid, 'rowcount': cursor.rowcount}
    else:
        # MySQL path
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if commit:
            db.commit()
        if fetch_one:
            result = cursor.fetchone()
            cursor.close()
            return result
        if fetch_all:
            results = cursor.fetchall()
            cursor.close()
            return results
        lastrowid = cursor.lastrowid
        rowcount = cursor.rowcount
        cursor.close()
        return {'lastrowid': lastrowid, 'rowcount': rowcount}


def close_db(e=None):
    """
    Close the database connection at the end of a request.
    Called automatically by Flask's teardown mechanism.
    """
    db = g.pop('db', None)
    g.pop('db_type', None)
    if db is not None:
        if hasattr(db, 'is_connected'):
            # MySQL connection
            if db.is_connected():
                db.close()
        else:
            # SQLite connection
            db.close()


def init_db():
    """
    Initialize the database by creating all tables, views, indexes, and triggers.

    For MySQL: Uses mysql.connector to execute DDL statements
    For SQLite: Uses sqlite3 to execute compatible DDL statements

    Both paths create the same logical schema:
      - STUDENT table (with AUTO_INCREMENT/AUTOINCREMENT PK)
      - FACULTY table
      - EVENT table (with FOREIGN KEY to FACULTY)
      - REGISTRATION table (with FOREIGN KEYs to STUDENT and EVENT)
      - Indexes on frequently queried columns
      - View: vw_event_participation
      - Trigger: trg_prevent_overbooking
    """
    db = get_db()
    db_type = get_db_type()

    if db_type == 'mysql':
        _init_mysql(db)
    else:
        _init_sqlite(db)


def _init_mysql(db):
    """Initialize MySQL schema with InnoDB tables, views, triggers, and indexes."""
    cursor = db.cursor()

    # --- Create Tables using InnoDB engine ---
    table_statements = [
        """CREATE TABLE IF NOT EXISTS STUDENT (
            Student_ID  INT             AUTO_INCREMENT,
            USN         VARCHAR(20)     UNIQUE NOT NULL,
            Name        VARCHAR(100)    NOT NULL,
            Dept        VARCHAR(50)     NOT NULL DEFAULT 'General',
            Email       VARCHAR(100)    UNIQUE NOT NULL,
            Password    VARCHAR(255)    NOT NULL,
            PRIMARY KEY (Student_ID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS FACULTY (
            Faculty_ID  INT             AUTO_INCREMENT,
            Name        VARCHAR(100)    NOT NULL,
            Dept        VARCHAR(50)     NOT NULL DEFAULT 'General',
            Email       VARCHAR(100)    UNIQUE NOT NULL,
            Password    VARCHAR(255)    NOT NULL,
            PRIMARY KEY (Faculty_ID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS EVENT (
            Event_ID    INT             AUTO_INCREMENT,
            Name        VARCHAR(200)    NOT NULL,
            Description TEXT            DEFAULT NULL,
            Date        DATE            NOT NULL,
            Venue       VARCHAR(200)    NOT NULL,
            Max_Seats   INT             DEFAULT 100,
            Faculty_ID  INT             DEFAULT NULL,
            PRIMARY KEY (Event_ID),
            CONSTRAINT fk_event_faculty
                FOREIGN KEY (Faculty_ID) REFERENCES FACULTY(Faculty_ID)
                ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS REGISTRATION (
            Reg_ID      INT         AUTO_INCREMENT,
            Student_ID  INT         NOT NULL,
            Event_ID    INT         NOT NULL,
            Reg_Time    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (Reg_ID),
            CONSTRAINT fk_reg_student
                FOREIGN KEY (Student_ID) REFERENCES STUDENT(Student_ID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT fk_reg_event
                FOREIGN KEY (Event_ID) REFERENCES EVENT(Event_ID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            UNIQUE KEY uq_student_event (Student_ID, Event_ID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
    ]

    for stmt in table_statements:
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"Table: {e}")

    db.commit()

    # --- Create Indexes ---
    for idx in [
        "CREATE INDEX idx_registration_student ON REGISTRATION(Student_ID)",
        "CREATE INDEX idx_registration_event ON REGISTRATION(Event_ID)",
        "CREATE INDEX idx_event_faculty ON EVENT(Faculty_ID)",
        "CREATE INDEX idx_event_date ON EVENT(Date)"
    ]:
        try:
            cursor.execute(idx)
        except Exception:
            pass
    db.commit()

    # --- Create VIEW ---
    try:
        cursor.execute("""
            CREATE OR REPLACE VIEW vw_event_participation AS
            SELECT E.Event_ID, E.Name AS Event_Name, E.Date AS Event_Date,
                   E.Venue, E.Max_Seats,
                   COALESCE(F.Name, 'Unassigned') AS Faculty_Name,
                   COUNT(R.Reg_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
            GROUP BY E.Event_ID, E.Name, E.Date, E.Venue, E.Max_Seats, F.Name
        """)
    except Exception as e:
        print(f"View: {e}")
    db.commit()

    # --- Create TRIGGER ---
    try:
        cursor.execute("DROP TRIGGER IF EXISTS trg_prevent_overbooking")
        cursor.execute("""
            CREATE TRIGGER trg_prevent_overbooking
            BEFORE INSERT ON REGISTRATION
            FOR EACH ROW
            BEGIN
                DECLARE current_count INT;
                DECLARE max_allowed INT;
                SELECT COUNT(*) INTO current_count FROM REGISTRATION WHERE Event_ID = NEW.Event_ID;
                SELECT Max_Seats INTO max_allowed FROM EVENT WHERE Event_ID = NEW.Event_ID;
                IF current_count >= max_allowed THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'EVENT_FULL: This event has reached maximum capacity.';
                END IF;
            END
        """)
    except Exception as e:
        print(f"Trigger: {e}")

    db.commit()
    cursor.close()


def _init_sqlite(db):
    """Initialize SQLite schema (fallback when MySQL is not available)."""
    db.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS STUDENT (
            Student_ID  INTEGER PRIMARY KEY AUTOINCREMENT,
            USN         TEXT    UNIQUE NOT NULL,
            Name        TEXT    NOT NULL,
            Dept        TEXT    NOT NULL DEFAULT 'General',
            Email       TEXT    UNIQUE NOT NULL,
            Password    TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS FACULTY (
            Faculty_ID  INTEGER PRIMARY KEY AUTOINCREMENT,
            Name        TEXT    NOT NULL,
            Dept        TEXT    NOT NULL DEFAULT 'General',
            Email       TEXT    UNIQUE NOT NULL,
            Password    TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS EVENT (
            Event_ID    INTEGER PRIMARY KEY AUTOINCREMENT,
            Name        TEXT    NOT NULL,
            Description TEXT    DEFAULT '',
            Date        TEXT    NOT NULL,
            Venue       TEXT    NOT NULL,
            Max_Seats   INTEGER DEFAULT 100,
            Faculty_ID  INTEGER,
            FOREIGN KEY (Faculty_ID) REFERENCES FACULTY(Faculty_ID)
                ON DELETE SET NULL ON UPDATE CASCADE
        );

        CREATE TABLE IF NOT EXISTS REGISTRATION (
            Reg_ID      INTEGER PRIMARY KEY AUTOINCREMENT,
            Student_ID  INTEGER NOT NULL,
            Event_ID    INTEGER NOT NULL,
            Timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (Student_ID) REFERENCES STUDENT(Student_ID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (Event_ID) REFERENCES EVENT(Event_ID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            UNIQUE(Student_ID, Event_ID)
        );

        CREATE INDEX IF NOT EXISTS idx_registration_student ON REGISTRATION(Student_ID);
        CREATE INDEX IF NOT EXISTS idx_registration_event   ON REGISTRATION(Event_ID);
        CREATE INDEX IF NOT EXISTS idx_event_faculty        ON EVENT(Faculty_ID);
        CREATE INDEX IF NOT EXISTS idx_event_date           ON EVENT(Date);

        CREATE VIEW IF NOT EXISTS vw_event_participation AS
        SELECT
            E.Event_ID,
            E.Name       AS Event_Name,
            E.Date       AS Event_Date,
            E.Venue,
            E.Max_Seats,
            F.Name       AS Faculty_Name,
            COUNT(R.Reg_ID) AS Participant_Count
        FROM EVENT E
        LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
        LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
        GROUP BY E.Event_ID;
    """)

    # SQLite trigger (uses RAISE instead of SIGNAL)
    try:
        db.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_prevent_overbooking
            BEFORE INSERT ON REGISTRATION
            BEGIN
                SELECT CASE
                    WHEN (SELECT COUNT(*) FROM REGISTRATION WHERE Event_ID = NEW.Event_ID)
                         >= (SELECT Max_Seats FROM EVENT WHERE Event_ID = NEW.Event_ID)
                    THEN RAISE(ABORT, 'EVENT_FULL: This event has reached maximum capacity.')
                END;
            END
        """)
    except Exception as e:
        print(f"SQLite trigger: {e}")

    db.commit()


def seed_db():
    """Populate the database with sample data from seed.sql."""
    db = get_db()
    db_type = get_db_type()

    with current_app.open_resource('database/seed.sql') as f:
        sql_script = f.read().decode('utf-8')

    if db_type == 'sqlite':
        # Convert MySQL syntax to SQLite
        sql_script = sql_script.replace('INSERT IGNORE', 'INSERT OR IGNORE')
        db.executescript(sql_script)
    else:
        cursor = db.cursor()
        statements = [s.strip() for s in sql_script.split(';\n') if s.strip()]
        for statement in statements:
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except Exception as e:
                    pass
        db.commit()
        cursor.close()
