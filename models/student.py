"""
models/student.py — Student Model (MySQL)
-------------------------------------------
Handles all database operations related to students using MySQL:
  - Create (INSERT with %s parameterized placeholders)
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
  - dictionary=True cursor for dict-like row access
"""

from database.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import IntegrityError


class Student:
    """Encapsulates CRUD operations for the STUDENT table in MySQL."""

    @staticmethod
    def create(usn, name, dept, email, password):
        """
        INSERT a new student into the MySQL database.

        MySQL Query: INSERT INTO STUDENT (USN, Name, Dept, Email, Password) VALUES (%s, %s, %s, %s, %s)

        Note: MySQL uses %s as parameter placeholder (not ? like SQLite).
        The mysql-connector-python driver handles proper escaping to prevent SQL injection.

        Args:
            usn (str): University Seat Number (primary identity)
            name (str): Student's full name
            dept (str): Department name
            email (str): Unique email address
            password (str): Plain-text password (will be hashed using werkzeug PBKDF2)

        Returns:
            int: The new student's AUTO_INCREMENT ID, or None if USN/email already exists.
        """
        db = get_db()
        cursor = db.cursor()
        hashed_pw = generate_password_hash(password)
        try:
            cursor.execute(
                "INSERT INTO STUDENT (USN, Name, Dept, Email, Password) VALUES (%s, %s, %s, %s, %s)",
                (usn.upper().strip(), name, dept, email, hashed_pw)
            )
            db.commit()
            return cursor.lastrowid  # Returns the AUTO_INCREMENT value
        except IntegrityError:
            # MySQL raises IntegrityError when UNIQUE constraint is violated
            # (duplicate USN or Email)
            db.rollback()
            return None
        finally:
            cursor.close()

    @staticmethod
    def find_by_email(email):
        """
        SELECT a student by their email address.

        MySQL Query: SELECT * FROM STUDENT WHERE Email = %s

        Args:
            email (str): Email to search for.

        Returns:
            dict or None: Student record as dictionary, or None if not found.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM STUDENT WHERE Email = %s", (email,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    @staticmethod
    def find_by_usn(usn):
        """
        SELECT a student by their USN (University Seat Number).

        MySQL Query: SELECT * FROM STUDENT WHERE USN = %s

        Args:
            usn (str): University Seat Number to search for.

        Returns:
            dict or None
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM STUDENT WHERE USN = %s", (usn.upper().strip(),)
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    @staticmethod
    def find_by_id(student_id):
        """
        SELECT a student by their primary key (AUTO_INCREMENT ID).

        MySQL Query: SELECT * FROM STUDENT WHERE Student_ID = %s

        Args:
            student_id (int): Student_ID (primary key)

        Returns:
            dict or None
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM STUDENT WHERE Student_ID = %s", (student_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    @staticmethod
    def get_all():
        """
        SELECT all students for admin panel display.

        MySQL Query: SELECT Student_ID, USN, Name, Dept, Email FROM STUDENT ORDER BY Name

        Returns:
            list[dict]: All students ordered alphabetically by name.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT Student_ID, USN, Name, Dept, Email FROM STUDENT ORDER BY Name"
        )
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def delete(student_id):
        """
        DELETE a student by ID.

        MySQL Query: DELETE FROM STUDENT WHERE Student_ID = %s

        Note: The FOREIGN KEY constraint with ON DELETE CASCADE automatically
        removes all related REGISTRATION rows when a student is deleted.
        This is enforced by InnoDB at the database engine level.

        Args:
            student_id (int): Student_ID to delete.

        Returns:
            bool: True if a student was deleted (cursor.rowcount > 0).
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM STUDENT WHERE Student_ID = %s", (student_id,)
        )
        db.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    @staticmethod
    def verify_password(stored_hash, password):
        """
        Verify a plain-text password against the stored PBKDF2 hash.

        Uses werkzeug's check_password_hash which supports:
          - PBKDF2-SHA256 with configurable iterations
          - Automatic salt extraction from the stored hash

        Args:
            stored_hash (str): Hashed password from MySQL DB
            password (str): Plain-text password to verify

        Returns:
            bool: True if password matches.
        """
        return check_password_hash(stored_hash, password)
