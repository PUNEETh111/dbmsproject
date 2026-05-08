"""
models/faculty.py — Faculty Model (MySQL)
-------------------------------------------
Handles all database operations related to faculty/admin users using MySQL:
  - Create (INSERT with parameterized %s placeholders)
  - Read (SELECT with WHERE clause)
  - Get all faculty (SELECT with ORDER BY)
  - Authentication support

MySQL Concepts Demonstrated:
  - %s parameterized queries for SQL injection prevention
  - IntegrityError handling for UNIQUE constraint violations
  - dictionary=True cursor for dict-like row access
  - cursor.lastrowid for AUTO_INCREMENT value retrieval
"""

from database.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import IntegrityError


class Faculty:
    """Encapsulates CRUD operations for the FACULTY table in MySQL."""

    @staticmethod
    def create(name, dept, email, password):
        """
        INSERT a new faculty member into MySQL.

        MySQL Query: INSERT INTO FACULTY (Name, Dept, Email, Password) VALUES (%s, %s, %s, %s)

        Args:
            name (str): Faculty name
            dept (str): Department
            email (str): Unique email
            password (str): Plain-text password (will be hashed)

        Returns:
            int: New Faculty_ID (AUTO_INCREMENT), or None on duplicate email.
        """
        db = get_db()
        cursor = db.cursor()
        hashed_pw = generate_password_hash(password)
        try:
            cursor.execute(
                "INSERT INTO FACULTY (Name, Dept, Email, Password) VALUES (%s, %s, %s, %s)",
                (name, dept, email, hashed_pw)
            )
            db.commit()
            return cursor.lastrowid
        except IntegrityError:
            db.rollback()
            return None
        finally:
            cursor.close()

    @staticmethod
    def find_by_email(email):
        """
        SELECT faculty by email address.

        MySQL Query: SELECT * FROM FACULTY WHERE Email = %s
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM FACULTY WHERE Email = %s", (email,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    @staticmethod
    def find_by_id(faculty_id):
        """
        SELECT faculty by primary key.

        MySQL Query: SELECT * FROM FACULTY WHERE Faculty_ID = %s
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM FACULTY WHERE Faculty_ID = %s", (faculty_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    @staticmethod
    def get_all():
        """
        SELECT all faculty members (used for dropdowns, admin views, etc.).

        MySQL Query: SELECT * FROM FACULTY ORDER BY Name
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM FACULTY ORDER BY Name")
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def verify_password(stored_hash, password):
        """Verify password against stored PBKDF2 hash."""
        return check_password_hash(stored_hash, password)
