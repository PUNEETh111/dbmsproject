-- ============================================================
-- Smart College Event Management System — MySQL Sample Data
-- ============================================================
-- ⚠️  WARNING: DO NOT USE THIS FILE DIRECTLY FOR SEEDING!
--    The password hashes below are PLACEHOLDERS and will NOT
--    validate with werkzeug's check_password_hash().
--    Use the Python seeder in app.py (calls seed_sample_data)
--    which generates valid password hashes at runtime.
-- ============================================================
-- Passwords: "password123" (only valid when seeded via Python)
-- ============================================================

-- ============================================================
-- MySQL INSERT Syntax Notes:
--   - INSERT IGNORE: Skips rows that would cause UNIQUE constraint
--     violations (equivalent to SQLite's INSERT OR IGNORE)
--   - Multi-row INSERT: MySQL supports inserting multiple rows
--     in a single INSERT statement for better performance
--   - %s placeholders: Used in Python for parameterized queries
--     (MySQL uses %s instead of SQLite's ?)
-- ============================================================

-- ============================================================
-- FACULTY (Admin Users)
-- Password: password123 (hashed via werkzeug at runtime)
-- ============================================================
INSERT IGNORE INTO FACULTY (Name, Dept, Email, Password) VALUES
('Dr. Ananya Sharma',  'Computer Science', 'ananya@college.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid'),
('Prof. Rajesh Kumar',  'Electronics',      'rajesh@college.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid'),
('Dr. Meena Iyer',      'Mathematics',      'meena@college.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid');

-- ============================================================
-- STUDENTS
-- Password: password123 (hashed via werkzeug at runtime)
-- ============================================================
INSERT IGNORE INTO STUDENT (USN, Name, Dept, Email, Password) VALUES
('1RV21CS001', 'Aarav Patel',    'Computer Science', 'aarav@student.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid'),
('1RV21EC015', 'Priya Singh',    'Electronics',      'priya@student.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid'),
('1RV21ME032', 'Rohit Verma',    'Mechanical',       'rohit@student.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid'),
('1RV21CS045', 'Sneha Reddy',    'Computer Science', 'sneha@student.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid'),
('1RV21CV008', 'Karan Mehta',    'Civil',            'karan@student.edu',
 'pbkdf2:sha256:600000$placeholder$placeholder_hash_not_valid');

-- ============================================================
-- EVENTS
-- Uses MySQL DATE type (YYYY-MM-DD format)
-- Faculty_ID references FACULTY table via FOREIGN KEY
-- ============================================================
INSERT IGNORE INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID) VALUES
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
-- REGISTRATIONS (Sample M:N relationships)
-- Each row creates a relationship between a Student and an Event
-- The UNIQUE constraint (Student_ID, Event_ID) prevents duplicates
-- The TRIGGER trg_prevent_overbooking checks seat capacity
-- ============================================================
INSERT IGNORE INTO REGISTRATION (Student_ID, Event_ID) VALUES
(1, 1), (1, 2), (1, 6),
(2, 1), (2, 3), (2, 4),
(3, 3), (3, 5), (3, 7),
(4, 1), (4, 2), (4, 6),
(5, 3), (5, 5), (5, 7);
