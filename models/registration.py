"""
models/registration.py — Registration Model (MySQL with SQLite Fallback)
--------------------------------------------------------------------------
Handles event registration operations:
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

MySQL JOIN Concepts Demonstrated:
  - INNER JOIN: Returns rows only when both tables have matching data
  - LEFT JOIN: Returns all rows from left table, NULL for unmatched right
  - Multi-table JOINs: Chaining JOINs across 3+ tables
"""

from database.db import execute_query, get_db, get_db_type


class Registration:
    """Encapsulates operations for the REGISTRATION table."""

    @staticmethod
    def register(student_id, event_id):
        """
        Register a student for an event using a TRANSACTION.

        Transaction Flow:
          1. START TRANSACTION / BEGIN (begin atomic operation)
          2. SELECT event details (verify event exists)
          3. INSERT INTO REGISTRATION (the trg_prevent_overbooking TRIGGER fires here)
          4. COMMIT (save changes) or ROLLBACK (undo on error)

        Returns:
            dict: {'success': bool, 'message': str, 'reg_id': int|None}
        """
        db = get_db()
        db_type = get_db_type()

        try:
            # --- START TRANSACTION ---
            if db_type == 'mysql':
                db.start_transaction()
            else:
                db.execute("BEGIN")

            # Step 1: Verify event exists
            event = execute_query(
                "SELECT Event_ID, Name, Max_Seats FROM EVENT WHERE Event_ID = %s",
                (event_id,), fetch_one=True
            )

            if not event:
                db.rollback()
                return {'success': False, 'message': 'Event not found.', 'reg_id': None}

            # Step 2: INSERT registration
            # The trg_prevent_overbooking TRIGGER fires BEFORE this INSERT
            if db_type == 'mysql':
                cursor = db.cursor(dictionary=True)
                cursor.execute(
                    "INSERT INTO REGISTRATION (Student_ID, Event_ID) VALUES (%s, %s)",
                    (student_id, event_id)
                )
                reg_id = cursor.lastrowid
                cursor.close()
            else:
                cursor = db.execute(
                    "INSERT INTO REGISTRATION (Student_ID, Event_ID) VALUES (?, ?)",
                    (student_id, event_id)
                )
                reg_id = cursor.lastrowid

            # --- COMMIT TRANSACTION ---
            db.commit()
            return {
                'success': True,
                'message': f'Successfully registered for {event["Name"]}!',
                'reg_id': reg_id
            }

        except Exception as e:
            # --- ROLLBACK TRANSACTION ---
            try:
                db.rollback()
            except Exception:
                pass

            error_msg = str(e)

            if 'UNIQUE' in error_msg or '1062' in error_msg or 'Duplicate' in error_msg:
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

        MySQL Query: DELETE FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s
        """
        result = execute_query(
            "DELETE FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s",
            (student_id, event_id),
            commit=True
        )
        return result['rowcount'] > 0

    @staticmethod
    def get_student_registrations(student_id):
        """
        SELECT all events a student is registered for.
        Uses multi-table JOIN: REGISTRATION ↔ EVENT ↔ FACULTY
        """
        db_type = get_db_type()
        # Use Reg_Time for MySQL, Timestamp for SQLite
        time_col = "R.Reg_Time AS Timestamp" if db_type == 'mysql' else "R.Timestamp"

        return execute_query(f"""
            SELECT
                R.Reg_ID,
                {time_col},
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
        """, (student_id,), fetch_all=True)

    @staticmethod
    def get_event_registrations(event_id):
        """
        SELECT all students registered for a specific event.
        Uses INNER JOIN: REGISTRATION ↔ STUDENT
        """
        db_type = get_db_type()
        time_col = "R.Reg_Time AS Timestamp" if db_type == 'mysql' else "R.Timestamp"

        return execute_query(f"""
            SELECT
                R.Reg_ID,
                {time_col},
                S.Student_ID,
                S.USN AS Student_USN,
                S.Name AS Student_Name,
                S.Dept AS Student_Dept,
                S.Email AS Student_Email
            FROM REGISTRATION R
            INNER JOIN STUDENT S ON R.Student_ID = S.Student_ID
            WHERE R.Event_ID = %s
            ORDER BY {time_col.split(' AS ')[0]} ASC
        """, (event_id,), fetch_all=True)

    @staticmethod
    def get_participant_counts():
        """
        GROUP BY query: Count participants per event.

        MySQL Aggregate Function:
          - COUNT(R.Reg_ID): Counts non-NULL Reg_ID values per group
          - GROUP BY E.Event_ID: Groups results by event
          - LEFT JOIN: Includes events with zero registrations
        """
        return execute_query("""
            SELECT
                E.Event_ID,
                E.Name AS Event_Name,
                COUNT(R.Reg_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
            GROUP BY E.Event_ID, E.Name
            ORDER BY Participant_Count DESC
        """, fetch_all=True)

    @staticmethod
    def is_registered(student_id, event_id):
        """
        Check if a student is already registered for an event.

        MySQL Query: SELECT 1 FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s
        """
        row = execute_query(
            "SELECT 1 FROM REGISTRATION WHERE Student_ID = %s AND Event_ID = %s",
            (student_id, event_id),
            fetch_one=True
        )
        return row is not None
