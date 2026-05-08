"""
app.py — Main Application Entry Point
Smart College Event Management System (MySQL Edition)

This Flask application uses MySQL as its RDBMS backend.
MySQL Concepts Demonstrated:
  - Database connection using mysql-connector-python
  - Table creation with InnoDB engine (ACID transactions)
  - AUTO_INCREMENT primary keys
  - FOREIGN KEY constraints with ON DELETE CASCADE / SET NULL
  - TRIGGERs for business logic enforcement
  - VIEWs for complex query encapsulation
  - INDEXes for query optimization
  - Parameterized queries (%s) for SQL injection prevention
  - Explicit TRANSACTION control (START TRANSACTION, COMMIT, ROLLBACK)
"""

import os
from flask import Flask, render_template, session
from config import Config
from database.db import get_db, close_db, init_db
from werkzeug.security import generate_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.teardown_appcontext(close_db)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.events import events_bp
    from routes.registrations import registrations_bp
    from routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(registrations_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def home():
        from models.event import Event
        events = Event.get_all()
        summary = Event.get_participation_summary()
        return render_template('home.html', events=events, summary=summary)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html', message='Page not found.'), 404

    @app.context_processor
    def inject_user():
        return {
            'current_user': {
                'id': session.get('user_id'),
                'name': session.get('user_name'),
                'type': session.get('user_type')
            }
        }

    return app


def create_database_if_needed():
    """
    Create the MySQL database if it doesn't exist.

    Uses mysql-connector-python to connect WITHOUT specifying a database,
    then runs CREATE DATABASE IF NOT EXISTS to ensure the database exists.
    """
    import mysql.connector
    from mysql.connector import Error as MySQLError

    try:
        conn_params = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'connection_timeout': 10
        }
        if Config.MYSQL_SSL:
            conn_params['ssl_disabled'] = False
            conn_params['ssl_verify_cert'] = False

        conn = mysql.connector.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}` "
                       f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
        print(f"✅ Database '{Config.MYSQL_DATABASE}' ready.")
    except MySQLError as e:
        print(f"⚠️  Could not create database: {e}")


def init_schema_with_trigger():
    """
    Initialize MySQL schema including TRIGGER creation.

    MySQL TRIGGERs require special handling:
      - The DELIMITER command is not supported by mysql-connector-python
      - TRIGGERs must be created in a separate cursor.execute() call
      - We first create tables/views, then create triggers separately
    """
    db = get_db()
    cursor = db.cursor()

    # --- Create Tables ---
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
                ON DELETE SET NULL
                ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS REGISTRATION (
            Reg_ID      INT         AUTO_INCREMENT,
            Student_ID  INT         NOT NULL,
            Event_ID    INT         NOT NULL,
            Reg_Time    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (Reg_ID),
            CONSTRAINT fk_reg_student
                FOREIGN KEY (Student_ID) REFERENCES STUDENT(Student_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            CONSTRAINT fk_reg_event
                FOREIGN KEY (Event_ID) REFERENCES EVENT(Event_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            UNIQUE KEY uq_student_event (Student_ID, Event_ID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
    ]

    for stmt in table_statements:
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"Table creation note: {e}")

    db.commit()

    # --- Create Indexes (ignore if already exist) ---
    index_statements = [
        "CREATE INDEX idx_registration_student ON REGISTRATION(Student_ID)",
        "CREATE INDEX idx_registration_event ON REGISTRATION(Event_ID)",
        "CREATE INDEX idx_event_faculty ON EVENT(Faculty_ID)",
        "CREATE INDEX idx_event_date ON EVENT(Date)"
    ]

    for stmt in index_statements:
        try:
            cursor.execute(stmt)
        except Exception:
            pass  # Index already exists

    db.commit()

    # --- Create VIEW ---
    try:
        cursor.execute("""
            CREATE OR REPLACE VIEW vw_event_participation AS
            SELECT
                E.Event_ID,
                E.Name       AS Event_Name,
                E.Date       AS Event_Date,
                E.Venue,
                E.Max_Seats,
                COALESCE(F.Name, 'Unassigned') AS Faculty_Name,
                COUNT(R.Reg_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
            GROUP BY E.Event_ID, E.Name, E.Date, E.Venue, E.Max_Seats, F.Name
        """)
    except Exception as e:
        print(f"View creation note: {e}")

    db.commit()

    # --- Create TRIGGER ---
    # MySQL TRIGGERs use SIGNAL SQLSTATE '45000' to raise custom errors
    # (unlike SQLite's RAISE(ABORT, ...))
    try:
        cursor.execute("DROP TRIGGER IF EXISTS trg_prevent_overbooking")
        cursor.execute("""
            CREATE TRIGGER trg_prevent_overbooking
            BEFORE INSERT ON REGISTRATION
            FOR EACH ROW
            BEGIN
                DECLARE current_count INT;
                DECLARE max_allowed INT;

                SELECT COUNT(*) INTO current_count
                FROM REGISTRATION
                WHERE Event_ID = NEW.Event_ID;

                SELECT Max_Seats INTO max_allowed
                FROM EVENT
                WHERE Event_ID = NEW.Event_ID;

                IF current_count >= max_allowed THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'EVENT_FULL: This event has reached maximum capacity.';
                END IF;
            END
        """)
    except Exception as e:
        print(f"Trigger creation note: {e}")

    db.commit()
    cursor.close()


def seed_sample_data():
    """
    Insert sample data with properly hashed passwords into MySQL.

    Uses parameterized INSERT with %s placeholders to prevent SQL injection.
    MySQL's INSERT IGNORE is used in production seed.sql, but here we use
    try/except to handle duplicates gracefully.
    """
    db = get_db()
    cursor = db.cursor()
    pw = generate_password_hash('password123')

    # --- INSERT Faculty ---
    faculty = [
        ('Dr. Ananya Sharma', 'Computer Science', 'ananya@college.edu'),
        ('Prof. Rajesh Kumar', 'Electronics', 'rajesh@college.edu'),
        ('Dr. Meena Iyer', 'Mathematics', 'meena@college.edu'),
    ]
    for n, d, e in faculty:
        try:
            cursor.execute(
                "INSERT INTO FACULTY (Name, Dept, Email, Password) VALUES (%s, %s, %s, %s)",
                (n, d, e, pw)
            )
        except Exception:
            pass

    # --- INSERT Students ---
    students = [
        ('1RV21CS001', 'Aarav Patel', 'Computer Science', 'aarav@student.edu'),
        ('1RV21EC015', 'Priya Singh', 'Electronics', 'priya@student.edu'),
        ('1RV21ME032', 'Rohit Verma', 'Mechanical', 'rohit@student.edu'),
        ('1RV21CS045', 'Sneha Reddy', 'Computer Science', 'sneha@student.edu'),
        ('1RV21CV008', 'Karan Mehta', 'Civil', 'karan@student.edu'),
    ]
    for usn, n, d, e in students:
        try:
            cursor.execute(
                "INSERT INTO STUDENT (USN, Name, Dept, Email, Password) VALUES (%s, %s, %s, %s, %s)",
                (usn, n, d, e, pw)
            )
        except Exception:
            pass

    # --- INSERT Events ---
    events = [
        ('TechFest 2024', 'Annual technology festival with coding competitions and hackathons.', '2024-11-15', 'Main Auditorium', 200, 1),
        ('AI & ML Workshop', 'Hands-on workshop on machine learning and neural networks.', '2024-11-20', 'CS Lab 101', 50, 1),
        ('Cultural Night', 'Grand evening of music, dance, and artistic performances.', '2024-12-01', 'Open Air Theatre', 500, 2),
        ('Robotics Expo', 'Exhibition of student-built robots, drones, and IoT projects.', '2024-12-10', 'ECE Block', 80, 2),
        ('Math Olympiad', 'Inter-college math competition on algebra and calculus.', '2024-12-15', 'Exam Hall A', 100, 3),
        ('Web Dev Bootcamp', 'Intensive bootcamp on HTML, CSS, JS, React, and Node.js.', '2025-01-10', 'CS Lab 202', 40, 1),
        ('Sports Day', 'Annual inter-department sports competition.', '2025-01-20', 'Sports Complex', 300, 3),
    ]
    for n, desc, dt, v, s, f in events:
        try:
            cursor.execute(
                "INSERT INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID) VALUES (%s, %s, %s, %s, %s, %s)",
                (n, desc, dt, v, s, f)
            )
        except Exception:
            pass

    # --- INSERT Registrations (M:N junction table entries) ---
    regs = [(1,1),(1,2),(1,6),(2,1),(2,3),(2,4),(3,3),(3,5),(3,7),(4,1),(4,2),(4,6),(5,3),(5,5),(5,7)]
    for sid, eid in regs:
        try:
            cursor.execute(
                "INSERT INTO REGISTRATION (Student_ID, Event_ID) VALUES (%s, %s)",
                (sid, eid)
            )
        except Exception:
            pass

    db.commit()
    cursor.close()


# --- Production: Module-level app for Gunicorn ---
# Gunicorn uses `gunicorn app:app` which needs this at module level
app = create_app()

# Auto-initialize MySQL database (works on both local and Render)
with app.app_context():
    try:
        # Step 1: Create database if it doesn't exist
        create_database_if_needed()

        # Step 2: Check if tables exist
        need_init = False
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT 1 FROM STUDENT LIMIT 1")
            cursor.fetchone()
            cursor.execute("SELECT 1 FROM EVENT LIMIT 1")
            cursor.fetchone()
            cursor.close()
        except Exception:
            need_init = True

        # Step 3: Initialize schema and seed data if needed
        if need_init:
            init_schema_with_trigger()
            seed_sample_data()
            print('✅ MySQL database initialized and seeded.')
    except Exception as e:
        print(f'⚠️  DB init note: {e}')


if __name__ == '__main__':
    print('\n🚀 Smart College Event Management System (MySQL Edition)')
    print(f'🗄️  MySQL: {Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DATABASE}')
    print('📍 http://127.0.0.1:5000')
    print('👤 Student: aarav@student.edu / password123 (USN: 1RV21CS001)')
    print('🧑‍🏫 Faculty: ananya@college.edu / password123\n')
    app.run(debug=True, port=5000)
