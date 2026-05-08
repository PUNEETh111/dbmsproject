"""
models/registration.py — Registration Model (MySQL)
-----------------------------------------------------
Handles event registration operations using MySQL:
  - Register (with explicit TRANSACTION control)
  - Unregister (DELETE with WHERE)
  - List registrations (multi-table JOIN queries)
  - Per-event participant listing

MySQL Transaction Concepts Demonstrated:
  - START TRANSACTION: Begins an explicit transaction
  - COMMIT: Saves all changes made during the transaction
  - ROLLBACK: Undoes all changes if an error occurs
  - ACID Properties:
    * Atomicity: Either all operations succeed or none do
    * Consistency: Database moves from one valid state to another
    * Isolation: Concurrent transactions don't interfere
    * Durability: Committed changes survive system failures
  - InnoDB row-level locking for concurrent access

MySQL JOIN Concepts Demonstrated:
  - INNER JOIN: Returns rows only when both tables have matching data
  - LEFT JOIN: Returns all rows from left table, NULL for unmatched right
  - Multi-table JOINs: Chaining JOINs across 3+ tables
"""

from database.db import get_db
from mysql.connector import IntegrityError, Error as MySQLError


class Registration:
    """Encapsulates operations for the REGISTRATION table in MySQL."""

    @staticmethod
    def register(student_id, event_id):
        """
        Register a student for an event using an explicit MySQL TRANSACTION.

        Transaction Flow:
          1. START TRANSACTION (begin atomic operation)
          2. SELECT event details (verify event exists)
          3. INSERT INTO REGISTRATION (the trg_prevent_overbooking TRIGGER fires here)
          4. COMMIT (save changes) or ROLLBACK (undo on error)

        MySQL Error Handling:
          - IntegrityError (errno 1062): Duplicate entry — student already registered
            (caught by UNIQUE KEY uq_student_event)
          - SIGNAL SQLSTATE '45000': Custom error from trg_prevent_overbooking trigger
            (event has reached maximum capacity)

        Args:
            student_id (int): Student registering
            event_id (int): Event to register for

        Returns:
            dict: {'success': bool, 'message': str, 'reg_id': int|None}
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # --- START TRANSACTION ---
            # In MySQL, START TRANSACTION explicitly begins a new transaction
            # All subsequent queries are part of this transaction until COMMIT/ROLLBACK
            db.start_transaction()

            # Step 1: Verify event exists (SELECT with WHERE)
            cursor.execute(
                "SELECT Event_ID, Name, Max_Seats FROM EVENT WHERE Event_ID = %s",
                (event_id,)
            )
            event = cursor.fetchone()

            if not event:
                db.rollback()
                cursor.close()
                return {'success': False, 'message': 'Event not found.', 'reg_id': None}

            # Step 2: INSERT registration
            # The trg_prevent_overbooking TRIGGER fires BEFORE this INSERT
            # If event is full, the trigger raises SIGNAL SQLSTATE '45000'
            cursor.execute(
                "INSERT INTO REGISTRATION (Student_ID, Event_ID) VALUES (%s, %s)",
                (student_id, event_id)
            )
            reg_id = cursor.lastrowid

            # --- COMMIT TRANSACTION ---
            # Saves all changes to disk permanently (Durability in ACID)
            db.commit()
            cursor.close()
            return {
                'success': True,
                'message': f'Successfully registered for {event["Name"]}!',
                'reg_id': reg_id
            }

        except IntegrityError as e:
            # --- ROLLBACK TRANSACTION ---
            # Undoes all changes made during this transaction (Atomicity in ACID)
            db.rollback()
            cursor.close()

            if e.errno == 1062:
                # MySQL error 1062: Duplicate entry for UNIQUE KEY
                return {
                    'success': False,
                    'message': 'You are already registered for this event.',
                    'reg_id': None
                }
            return {
                'success': False,
                'message': f'Registration failed: {str(e)}',
                'reg_id': None
            }

        except MySQLError as e:
            db.rollback()
            cursor.close()
            error_msg = str(e)

            if 'EVENT_FULL' in error_msg:
                return {
                    'success': False,
                    'message': 'Sorry, this event has reached maximum capacity.',
                    'reg_id': None
                }
            return {
                'success': False,
                'message': f'Registration failed: {error_msg}',
                'reg_id': None
            }

    @staticmethod
    def unregister(student_id, event_id):
        """
        DELETE a registration (unregister student from event).

        MySQL Query: DELETE FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s

        Args:
            student_id (int): Student's ID
            event_id (int): Event's ID

        Returns:
            bool: True if a registration was removed (cursor.rowcount > 0).
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s",
            (student_id, event_id)
        )
        db.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    @staticmethod
    def get_student_registrations(student_id):
        """
        SELECT all events a student is registered for.

        Multi-table JOIN:
          REGISTRATION ↔ EVENT ↔ FACULTY (3-table join)

        MySQL Query:
            SELECT R.Reg_ID, R.Reg_Time, E.Event_ID, E.Name, E.Date, E.Venue, F.Name
            FROM REGISTRATION R
            INNER JOIN EVENT E ON R.Event_ID = E.Event_ID
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            WHERE R.Student_ID = %s
            ORDER BY E.Date ASC

        JOIN Types Used:
          - INNER JOIN (REGISTRATION ↔ EVENT): Only returns registrations with valid events
          - LEFT JOIN (EVENT ↔ FACULTY): Returns events even if faculty was deleted (NULL)

        Args:
            student_id (int): Student's ID

        Returns:
            list[dict]: Registered events with details.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                R.Reg_ID,
                R.Reg_Time AS Timestamp,
                E.Event_ID,
                E.Name AS Event_Name,
                E.Date AS Event_Date,
                E.Venue,
                COALESCE(F.Name, 'Unassigned') AS Faculty_Name
            FROM REGISTRATION R
            INNER JOIN EVENT E ON R.Event_ID = E.Event_ID
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            WHERE R.Student_ID = %s
            ORDER BY E.Date ASC
        """, (student_id,))
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def get_event_registrations(event_id):
        """
        SELECT all students registered for a specific event.

        Uses INNER JOIN: REGISTRATION ↔ STUDENT
        (only returns registrations with valid student records)

        MySQL Query:
            SELECT R.Reg_ID, R.Reg_Time, S.Student_ID, S.USN, S.Name, S.Dept, S.Email
            FROM REGISTRATION R
            INNER JOIN STUDENT S ON R.Student_ID = S.Student_ID
            WHERE R.Event_ID = %s
            ORDER BY R.Reg_Time ASC

        Args:
            event_id (int): Event's ID

        Returns:
            list[dict]: Registered students with details.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                R.Reg_ID,
                R.Reg_Time AS Timestamp,
                S.Student_ID,
                S.USN AS Student_USN,
                S.Name AS Student_Name,
                S.Dept AS Student_Dept,
                S.Email AS Student_Email
            FROM REGISTRATION R
            INNER JOIN STUDENT S ON R.Student_ID = S.Student_ID
            WHERE R.Event_ID = %s
            ORDER BY R.Reg_Time ASC
        """, (event_id,))
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def get_participant_counts():
        """
        GROUP BY query: Count participants per event.

        MySQL Aggregate Function:
          - COUNT(R.Reg_ID): Counts non-NULL Reg_ID values per group
          - GROUP BY E.Event_ID: Groups results by event
          - LEFT JOIN: Includes events with zero registrations

        MySQL Query:
            SELECT E.Event_ID, E.Name, COUNT(R.Reg_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
            GROUP BY E.Event_ID
            ORDER BY Participant_Count DESC

        Returns:
            list[dict]: Event names with participant counts.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                E.Event_ID,
                E.Name AS Event_Name,
                COUNT(R.Reg_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
            GROUP BY E.Event_ID, E.Name
            ORDER BY Participant_Count DESC
        """)
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def is_registered(student_id, event_id):
        """
        Check if a student is already registered for an event.

        MySQL Query: SELECT 1 FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s

        Note: Using SELECT 1 (instead of SELECT *) is a MySQL optimization —
        we only need to know if a row exists, not fetch its data.

        Returns:
            bool: True if registered.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT 1 FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s",
            (student_id, event_id)
        )
        row = cursor.fetchone()
        cursor.close()
        return row is not None
