"""
models/student.py — Student Model
-----------------------------------
Handles all database operations related to students:
  - Create (register with USN)
  - Read (find by ID, email, USN)
  - Get all students
  - Authentication support
"""

import sqlite3
from database.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash


class Student:
    """Encapsulates CRUD operations for the STUDENT table."""

    @staticmethod
    def create(usn, name, dept, email, password):
        """
        INSERT a new student into the database.

        Args:
            usn (str): University Seat Number (primary identity)
            name (str): Student's full name
            dept (str): Department name
            email (str): Unique email address
            password (str): Plain-text password (will be hashed)

        Returns:
            int: The new student's ID, or None if USN/email already exists.
        """
        db = get_db()
        hashed_pw = generate_password_hash(password)
        try:
            cursor = db.execute(
                "INSERT INTO STUDENT (USN, Name, Dept, Email, Password) VALUES (?, ?, ?, ?, ?)",
                (usn.upper().strip(), name, dept, email, hashed_pw)
            )
            db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # UNIQUE constraint violated (duplicate USN or email)
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
    def find_by_usn(usn):
        """
        SELECT a student by their USN.

        Args:
            usn (str): University Seat Number to search for.

        Returns:
            sqlite3.Row or None
        """
        db = get_db()
        return db.execute(
            "SELECT * FROM STUDENT WHERE USN = ?", (usn.upper().strip(),)
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
    def get_all():
        """
        SELECT all students (for admin panel).

        Returns:
            list[sqlite3.Row]: All students ordered by name.
        """
        db = get_db()
        return db.execute(
            "SELECT Student_ID, USN, Name, Dept, Email FROM STUDENT ORDER BY Name"
        ).fetchall()

    @staticmethod
    def delete(student_id):
        """
        DELETE a student by ID. Cascading FK deletes related registrations.

        Args:
            student_id (int): Student_ID to delete.

        Returns:
            bool: True if a student was deleted.
        """
        db = get_db()
        cursor = db.execute(
            "DELETE FROM STUDENT WHERE Student_ID = ?", (student_id,)
        )
        db.commit()
        return cursor.rowcount > 0

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
