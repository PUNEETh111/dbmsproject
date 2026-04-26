"""
app.py — Main Application Entry Point
Smart College Event Management System
"""

import os
from flask import Flask, render_template, session
from config import Config
from database.db import get_db, close_db, init_db
from werkzeug.security import generate_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
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
        return render_template('home.html', events=events[:6], summary=summary)

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
    """Insert sample data with properly hashed passwords."""
    db = get_db()
    pw = generate_password_hash('password123')

    faculty = [
        ('Dr. Ananya Sharma', 'Computer Science', 'ananya@college.edu'),
        ('Prof. Rajesh Kumar', 'Electronics', 'rajesh@college.edu'),
        ('Dr. Meena Iyer', 'Mathematics', 'meena@college.edu'),
    ]
    for n, d, e in faculty:
        try:
            db.execute("INSERT INTO FACULTY (Name,Dept,Email,Password) VALUES (?,?,?,?)", (n,d,e,pw))
        except Exception:
            pass

    students = [
        ('Aarav Patel', 'Computer Science', 'aarav@student.edu'),
        ('Priya Singh', 'Electronics', 'priya@student.edu'),
        ('Rohit Verma', 'Mechanical', 'rohit@student.edu'),
        ('Sneha Reddy', 'Computer Science', 'sneha@student.edu'),
        ('Karan Mehta', 'Civil', 'karan@student.edu'),
    ]
    for n, d, e in students:
        try:
            db.execute("INSERT INTO STUDENT (Name,Dept,Email,Password) VALUES (?,?,?,?)", (n,d,e,pw))
        except Exception:
            pass

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
            db.execute("INSERT INTO EVENT (Name,Description,Date,Venue,Max_Seats,Faculty_ID) VALUES (?,?,?,?,?,?)", (n,desc,dt,v,s,f))
        except Exception:
            pass

    regs = [(1,1),(1,2),(1,6),(2,1),(2,3),(2,4),(3,3),(3,5),(3,7),(4,1),(4,2),(4,6),(5,3),(5,5),(5,7)]
    for sid, eid in regs:
        try:
            db.execute("INSERT INTO REGISTRATION (Student_ID,Event_ID) VALUES (?,?)", (sid,eid))
        except Exception:
            pass
    db.commit()


if __name__ == '__main__':
    app = create_app()
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
            print('Database created and seeded.')

    print('\n🚀 Smart College Event Management System')
    print('📍 http://127.0.0.1:5000')
    print('👤 Student: aarav@student.edu / password123')
    print('🧑‍🏫 Faculty: ananya@college.edu / password123\n')
    app.run(debug=True, port=5000)
