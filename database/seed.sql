-- ============================================================
-- Smart College Event Management System — Sample Data
-- ============================================================
-- ⚠️  WARNING: DO NOT USE THIS FILE DIRECTLY FOR SEEDING!
--    The password hashes below are PLACEHOLDERS and will NOT
--    validate with werkzeug's check_password_hash().
--    Use the Python seeder: python app.py (calls seed_sample_data)
--    which generates valid hashes at runtime.
-- ============================================================
-- Passwords: "password123" (only valid when seeded via Python)
-- ============================================================

-- ============================================================
-- FACULTY (Admin Users)
-- Password: password123
-- ============================================================
INSERT OR IGNORE INTO FACULTY (Name, Dept, Email, Password) VALUES
('Dr. Ananya Sharma',  'Computer Science', 'ananya@college.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e'),
('Prof. Rajesh Kumar',  'Electronics',      'rajesh@college.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e'),
('Dr. Meena Iyer',      'Mathematics',      'meena@college.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e');

-- ============================================================
-- STUDENTS
-- Password: password123
-- ============================================================
INSERT OR IGNORE INTO STUDENT (Name, Dept, Email, Password) VALUES
('Aarav Patel',    'Computer Science', 'aarav@student.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e'),
('Priya Singh',    'Electronics',      'priya@student.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e'),
('Rohit Verma',    'Mechanical',       'rohit@student.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e'),
('Sneha Reddy',    'Computer Science', 'sneha@student.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e'),
('Karan Mehta',    'Civil',            'karan@student.edu',
 'pbkdf2:sha256:600000$salt$e24d55d8b5d0e5ec7b3d9b9d5f6a8c3e1d2f4a6b8c0e2f4a6b8c0e2f4a6b8c0e');

-- ============================================================
-- EVENTS
-- ============================================================
INSERT OR IGNORE INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID) VALUES
('TechFest 2024',
 'Annual technology festival featuring coding competitions, hackathons, and tech talks from industry leaders.',
 '2024-11-15', 'Main Auditorium', 200, 1),

('AI & ML Workshop',
 'Hands-on workshop covering machine learning fundamentals, neural networks, and real-world AI applications.',
 '2024-11-20', 'CS Lab 101', 50, 1),

('Cultural Night',
 'A grand evening of music, dance, drama, and artistic performances by students across all departments.',
 '2024-12-01', 'Open Air Theatre', 500, 2),

('Robotics Expo',
 'Exhibition showcasing student-built robots, drones, and IoT projects with live demonstrations.',
 '2024-12-10', 'ECE Block', 80, 2),

('Math Olympiad',
 'Inter-college mathematics competition testing problem-solving skills across algebra, calculus, and combinatorics.',
 '2024-12-15', 'Exam Hall A', 100, 3),

('Web Dev Bootcamp',
 'Three-day intensive bootcamp on modern web development with HTML, CSS, JavaScript, React, and Node.js.',
 '2025-01-10', 'CS Lab 202', 40, 1),

('Sports Day',
 'Annual inter-department sports competition featuring athletics, cricket, football, and indoor games.',
 '2025-01-20', 'Sports Complex', 300, 3);

-- ============================================================
-- REGISTRATIONS (Sample)
-- ============================================================
INSERT OR IGNORE INTO REGISTRATION (Student_ID, Event_ID) VALUES
(1, 1), (1, 2), (1, 6),
(2, 1), (2, 3), (2, 4),
(3, 3), (3, 5), (3, 7),
(4, 1), (4, 2), (4, 6),
(5, 3), (5, 5), (5, 7);
