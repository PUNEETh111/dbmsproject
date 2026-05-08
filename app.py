"""
app.py — Main Application Entry Point
Smart College Event Management System (MySQL Edition)

This Flask application uses MySQL as its primary RDBMS backend,
with automatic SQLite fallback for zero-configuration deployment.

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
from database.db import get_db, close_db, init_db, get_db_type, is_mysql_configured
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


def seed_sample_data():
    """
    Insert sample data with properly hashed passwords.

    Uses parameterized queries with %s placeholders (auto-converted
    to ? for SQLite by the execute_query helper).
    """
    from database.db import execute_query

    pw = generate_password_hash('password123')

    # --- INSERT Faculty ---
    faculty = [
        ('Dr. Ananya Sharma', 'Computer Science', 'ananya@college.edu'),
        ('Prof. Rajesh Kumar', 'Electronics', 'rajesh@college.edu'),
        ('Dr. Meena Iyer', 'Mathematics', 'meena@college.edu'),
    ]
    for n, d, e in faculty:
        try:
            execute_query(
                "INSERT INTO FACULTY (Name, Dept, Email, Password) VALUES (%s, %s, %s, %s)",
                (n, d, e, pw), commit=True
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
            execute_query(
                "INSERT INTO STUDENT (USN, Name, Dept, Email, Password) VALUES (%s, %s, %s, %s, %s)",
                (usn, n, d, e, pw), commit=True
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
            execute_query(
                "INSERT INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID) VALUES (%s, %s, %s, %s, %s, %s)",
                (n, desc, dt, v, s, f), commit=True
            )
        except Exception:
            pass

    # --- INSERT Registrations (M:N junction table entries) ---
    regs = [(1,1),(1,2),(1,6),(2,1),(2,3),(2,4),(3,3),(3,5),(3,7),(4,1),(4,2),(4,6),(5,3),(5,5),(5,7)]
    for sid, eid in regs:
        try:
            execute_query(
                "INSERT INTO REGISTRATION (Student_ID, Event_ID) VALUES (%s, %s)",
                (sid, eid), commit=True
            )
        except Exception:
            pass


# --- Production: Module-level app for Gunicorn ---
app = create_app()

# Auto-initialize database (works on both local and Render)
with app.app_context():
    try:
        need_init = False

        try:
            from database.db import execute_query
            execute_query("SELECT 1 FROM STUDENT LIMIT 1", fetch_one=True)
            execute_query("SELECT 1 FROM EVENT LIMIT 1", fetch_one=True)
            db_type = get_db_type()
            print(f'✅ Database OK ({db_type.upper()})')
        except Exception:
            need_init = True

        if need_init:
            init_db()
            seed_sample_data()
            db_type = get_db_type()
            print(f'✅ Database initialized and seeded ({db_type.upper()})')
    except Exception as e:
        print(f'⚠️  DB init note: {e}')


if __name__ == '__main__':
    print('\n🚀 Smart College Event Management System (MySQL Edition)')
    print('📍 http://127.0.0.1:5000')
    print('👤 Student: aarav@student.edu / password123 (USN: 1RV21CS001)')
    print('🧑‍🏫 Faculty: ananya@college.edu / password123\n')
    app.run(debug=True, port=5000)
