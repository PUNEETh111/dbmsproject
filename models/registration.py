"""
models/registration.py — Registration Model
---------------------------------------------
Handles event registration operations:
  - Register (with TRANSACTION)
  - Unregister
  - List registrations (JOIN queries)
  - Per-event participant listing
"""

from database.db import get_db


class Registration:
    """Encapsulates operations for the REGISTRATION table."""

    @staticmethod
    def register(student_id, event_id):
        """
        Register a student for an event using a TRANSACTION.

        This method uses BEGIN/COMMIT/ROLLBACK to ensure atomicity:
          1. Check if event exists
          2. Insert registration (trigger handles overbooking check)
          3. Commit on success, rollback on failure

        Args:
            student_id (int): Student registering
            event_id (int): Event to register for

        Returns:
            dict: {'success': bool, 'message': str, 'reg_id': int|None}
        """
        db = get_db()
        try:
            # --- BEGIN TRANSACTION ---
            db.execute("BEGIN")

            # Verify event exists
            event = db.execute(
                "SELECT Event_ID, Name, Max_Seats FROM EVENT WHERE Event_ID = ?",
                (event_id,)
            ).fetchone()

            if not event:
                db.execute("ROLLBACK")
                return {'success': False, 'message': 'Event not found.', 'reg_id': None}

            # Insert registration
            # The trg_prevent_overbooking TRIGGER will fire here
            cursor = db.execute(
                "INSERT INTO REGISTRATION (Student_ID, Event_ID) VALUES (?, ?)",
                (student_id, event_id)
            )

            # --- COMMIT TRANSACTION ---
            db.execute("COMMIT")
            return {
                'success': True,
                'message': f'Successfully registered for {event["Name"]}!',
                'reg_id': cursor.lastrowid
            }

        except Exception as e:
            # --- ROLLBACK TRANSACTION ---
            db.execute("ROLLBACK")
            error_msg = str(e)

            if 'UNIQUE constraint failed' in error_msg:
                return {
                    'success': False,
                    'message': 'You are already registered for this event.',
                    'reg_id': None
                }
            elif 'EVENT_FULL' in error_msg:
                return {
                    'success': False,
                    'message': 'Sorry, this event has reached maximum capacity.',
                    'reg_id': None
                }
            else:
                return {
                    'success': False,
                    'message': f'Registration failed: {error_msg}',
                    'reg_id': None
                }

    @staticmethod
    def unregister(student_id, event_id):
        """
        DELETE a registration (unregister student from event).

        Args:
            student_id (int): Student's ID
            event_id (int): Event's ID

        Returns:
            bool: True if a registration was removed.
        """
        db = get_db()
        cursor = db.execute(
            "DELETE FROM REGISTRATION WHERE Student_ID = ? AND Event_ID = ?",
            (student_id, event_id)
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def get_student_registrations(student_id):
        """
        SELECT all events a student is registered for.
        Uses JOIN: REGISTRATION ↔ EVENT ↔ FACULTY

        Args:
            student_id (int): Student's ID

        Returns:
            list[sqlite3.Row]: Registered events with details.
        """
        db = get_db()
        return db.execute("""
            SELECT
                R.Reg_ID,
                R.Timestamp,
                E.Event_ID,
                E.Name AS Event_Name,
                E.Date AS Event_Date,
                E.Venue,
                COALESCE(F.Name, 'Unassigned') AS Faculty_Name
            FROM REGISTRATION R
            INNER JOIN EVENT E ON R.Event_ID = E.Event_ID
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            WHERE R.Student_ID = ?
            ORDER BY E.Date ASC
        """, (student_id,)).fetchall()

    @staticmethod
    def get_event_registrations(event_id):
        """
        SELECT all students registered for a specific event.
        Uses JOIN: REGISTRATION ↔ STUDENT

        Args:
            event_id (int): Event's ID

        Returns:
            list[sqlite3.Row]: Registered students with details.
        """
        db = get_db()
        return db.execute("""
            SELECT
                R.Reg_ID,
                R.Timestamp,
                S.Student_ID,
                S.Name AS Student_Name,
                S.Dept AS Student_Dept,
                S.Email AS Student_Email
            FROM REGISTRATION R
            INNER JOIN STUDENT S ON R.Student_ID = S.Student_ID
            WHERE R.Event_ID = ?
            ORDER BY R.Timestamp ASC
        """, (event_id,)).fetchall()

    @staticmethod
    def get_participant_counts():
        """
        GROUP BY query: Count participants per event.

        Returns:
            list[sqlite3.Row]: Event names with participant counts.
        """
        db = get_db()
        return db.execute("""
            SELECT
                E.Event_ID,
                E.Name AS Event_Name,
                COUNT(R.Reg_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
            GROUP BY E.Event_ID
            ORDER BY Participant_Count DESC
        """).fetchall()

    @staticmethod
    def is_registered(student_id, event_id):
        """
        Check if a student is already registered for an event.

        Returns:
            bool: True if registered.
        """
        db = get_db()
        row = db.execute(
            "SELECT 1 FROM REGISTRATION WHERE Student_ID = ? AND Event_ID = ?",
            (student_id, event_id)
        ).fetchone()
        return row is not None
