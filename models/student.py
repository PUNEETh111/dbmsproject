"""
models/student.py — Student Model
-----------------------------------
Handles all database operations related to students:
  - Create (register)
  - Read (find by ID, email)
  - Authentication support
"""

import sqlite3
from database.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash


class Student:
    """Encapsulates CRUD operations for the STUDENT table."""

    @staticmethod
    def create(name, dept, email, password):
        """
        INSERT a new student into the database.

        Args:
            name (str): Student's full name
            dept (str): Department name
            email (str): Unique email address
            password (str): Plain-text password (will be hashed)

        Returns:
            int: The new student's ID, or None if email already exists.
        """
        db = get_db()
        hashed_pw = generate_password_hash(password)
        try:
            cursor = db.execute(
                "INSERT INTO STUDENT (Name, Dept, Email, Password) VALUES (?, ?, ?, ?)",
                (name, dept, email, hashed_pw)
            )
            db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # UNIQUE constraint violated (duplicate email)
            return None

    @staticmethod
    def find_by_email(email):
        """
        SELECT a student by their email address.

        Args:
            email (str): Email to search for.

        Returns:
            sqlite3.Row or None
        """
        db = get_db()
        return db.execute(
            "SELECT * FROM STUDENT WHERE Email = ?", (email,)
        ).fetchone()

    @staticmethod
    def find_by_id(student_id):
        """
        SELECT a student by their primary key.

        Args:
            student_id (int): Student_ID

        Returns:
            sqlite3.Row or None
        """
        db = get_db()
        return db.execute(
            "SELECT * FROM STUDENT WHERE Student_ID = ?", (student_id,)
        ).fetchone()

    @staticmethod
    def verify_password(stored_hash, password):
        """
        Verify a plain-text password against the stored hash.

        Args:
            stored_hash (str): Hashed password from DB
            password (str): Plain-text password to verify

        Returns:
            bool: True if password matches.
        """
        return check_password_hash(stored_hash, password)
