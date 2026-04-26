"""
models/faculty.py — Faculty Model
-----------------------------------
Handles all database operations related to faculty/admin users:
  - Create
  - Read (find by ID, email)
  - Authentication support
"""

import sqlite3
from database.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash


class Faculty:
    """Encapsulates CRUD operations for the FACULTY table."""

    @staticmethod
    def create(name, dept, email, password):
        """
        INSERT a new faculty member.

        Args:
            name (str): Faculty name
            dept (str): Department
            email (str): Unique email
            password (str): Plain-text password (will be hashed)

        Returns:
            int: New Faculty_ID, or None on duplicate email.
        """
        db = get_db()
        hashed_pw = generate_password_hash(password)
        try:
            cursor = db.execute(
                "INSERT INTO FACULTY (Name, Dept, Email, Password) VALUES (?, ?, ?, ?)",
                (name, dept, email, hashed_pw)
            )
            db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    @staticmethod
    def find_by_email(email):
        """SELECT faculty by email."""
        db = get_db()
        return db.execute(
            "SELECT * FROM FACULTY WHERE Email = ?", (email,)
        ).fetchone()

    @staticmethod
    def find_by_id(faculty_id):
        """SELECT faculty by primary key."""
        db = get_db()
        return db.execute(
            "SELECT * FROM FACULTY WHERE Faculty_ID = ?", (faculty_id,)
        ).fetchone()

    @staticmethod
    def get_all():
        """SELECT all faculty members (for dropdowns, etc.)."""
        db = get_db()
        return db.execute("SELECT * FROM FACULTY ORDER BY Name").fetchall()

    @staticmethod
    def verify_password(stored_hash, password):
        """Verify password against stored hash."""
        return check_password_hash(stored_hash, password)
