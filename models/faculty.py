"""
models/faculty.py — Faculty Model (MySQL with SQLite Fallback)
----------------------------------------------------------------
Handles all database operations related to faculty/admin users:
  - Create (INSERT with parameterized %s placeholders)
  - Read (SELECT with WHERE clause)
  - Get all faculty (SELECT with ORDER BY)
  - Authentication support

MySQL Concepts Demonstrated:
  - %s parameterized queries for SQL injection prevention
  - IntegrityError handling for UNIQUE constraint violations
  - dictionary cursor for dict-like row access
  - cursor.lastrowid for AUTO_INCREMENT value retrieval
"""

from database.db import execute_query, get_db
from werkzeug.security import generate_password_hash, check_password_hash


class Faculty:
    """Encapsulates CRUD operations for the FACULTY table."""

    @staticmethod
    def create(name, dept, email, password):
        """
        INSERT a new faculty member.

        MySQL Query: INSERT INTO FACULTY (Name, Dept, Email, Password) VALUES (%s, %s, %s, %s)

        Returns:
            int: New Faculty_ID (AUTO_INCREMENT), or None on duplicate email.
        """
        hashed_pw = generate_password_hash(password)
        try:
            result = execute_query(
                "INSERT INTO FACULTY (Name, Dept, Email, Password) VALUES (%s, %s, %s, %s)",
                (name, dept, email, hashed_pw),
                commit=True
            )
            return result['lastrowid']
        except Exception:
            try:
                get_db().rollback()
            except Exception:
                pass
            return None

    @staticmethod
    def find_by_email(email):
        """SELECT faculty by email. MySQL Query: SELECT * FROM FACULTY WHERE Email = %s"""
        return execute_query(
            "SELECT * FROM FACULTY WHERE Email = %s", (email,),
            fetch_one=True
        )

    @staticmethod
    def find_by_id(faculty_id):
        """SELECT faculty by primary key. MySQL Query: SELECT * FROM FACULTY WHERE Faculty_ID = %s"""
        return execute_query(
            "SELECT * FROM FACULTY WHERE Faculty_ID = %s", (faculty_id,),
            fetch_one=True
        )

    @staticmethod
    def get_all():
        """SELECT all faculty members. MySQL Query: SELECT * FROM FACULTY ORDER BY Name"""
        return execute_query(
            "SELECT * FROM FACULTY ORDER BY Name",
            fetch_all=True
        )

    @staticmethod
    def verify_password(stored_hash, password):
        """Verify password against stored PBKDF2 hash."""
        return check_password_hash(stored_hash, password)
