"""
models/student.py — Student Model (MySQL with SQLite Fallback)
----------------------------------------------------------------
Handles all database operations related to students:
  - Create (INSERT with parameterized placeholders)
  - Read (SELECT with WHERE clause)
  - Get all students (SELECT with ORDER BY)
  - Delete (DELETE with WHERE — CASCADE removes registrations)
  - Authentication support (password hashing with werkzeug)

MySQL Concepts Demonstrated:
  - Parameterized queries using %s (prevents SQL injection)
  - AUTO_INCREMENT for Student_ID generation
  - UNIQUE constraints on USN and Email (IntegrityError on duplicates)
  - cursor.fetchone() / cursor.fetchall() for retrieving result sets
  - cursor.lastrowid to get the AUTO_INCREMENT value after INSERT
"""

from database.db import execute_query, get_db, get_db_type
from werkzeug.security import generate_password_hash, check_password_hash


class Student:
    """Encapsulates CRUD operations for the STUDENT table."""

    @staticmethod
    def create(usn, name, dept, email, password):
        """
        INSERT a new student into the database.

        MySQL Query: INSERT INTO STUDENT (USN, Name, Dept, Email, Password) VALUES (%s, %s, %s, %s, %s)

        Note: %s placeholders are auto-converted to ? for SQLite compatibility.

        Returns:
            int: The new student's AUTO_INCREMENT ID, or None if USN/email already exists.
        """
        hashed_pw = generate_password_hash(password)
        try:
            result = execute_query(
                "INSERT INTO STUDENT (USN, Name, Dept, Email, Password) VALUES (%s, %s, %s, %s, %s)",
                (usn.upper().strip(), name, dept, email, hashed_pw),
                commit=True
            )
            return result['lastrowid']
        except Exception:
            # UNIQUE constraint violated (duplicate USN or email)
            try:
                get_db().rollback()
            except Exception:
                pass
            return None

    @staticmethod
    def find_by_email(email):
        """
        SELECT a student by their email address.

        MySQL Query: SELECT * FROM STUDENT WHERE Email = %s
        """
        return execute_query(
            "SELECT * FROM STUDENT WHERE Email = %s", (email,),
            fetch_one=True
        )

    @staticmethod
    def find_by_usn(usn):
        """
        SELECT a student by their USN (University Seat Number).

        MySQL Query: SELECT * FROM STUDENT WHERE USN = %s
        """
        return execute_query(
            "SELECT * FROM STUDENT WHERE USN = %s", (usn.upper().strip(),),
            fetch_one=True
        )

    @staticmethod
    def find_by_id(student_id):
        """
        SELECT a student by their primary key (AUTO_INCREMENT ID).

        MySQL Query: SELECT * FROM STUDENT WHERE Student_ID = %s
        """
        return execute_query(
            "SELECT * FROM STUDENT WHERE Student_ID = %s", (student_id,),
            fetch_one=True
        )

    @staticmethod
    def get_all():
        """
        SELECT all students for admin panel display.

        MySQL Query: SELECT Student_ID, USN, Name, Dept, Email FROM STUDENT ORDER BY Name
        """
        return execute_query(
            "SELECT Student_ID, USN, Name, Dept, Email FROM STUDENT ORDER BY Name",
            fetch_all=True
        )

    @staticmethod
    def delete(student_id):
        """
        DELETE a student by ID.

        MySQL Query: DELETE FROM STUDENT WHERE Student_ID = %s

        Note: ON DELETE CASCADE removes related REGISTRATION rows automatically.
        """
        result = execute_query(
            "DELETE FROM STUDENT WHERE Student_ID = %s", (student_id,),
            commit=True
        )
        return result['rowcount'] > 0

    @staticmethod
    def verify_password(stored_hash, password):
        """Verify a plain-text password against the stored PBKDF2 hash."""
        return check_password_hash(stored_hash, password)
