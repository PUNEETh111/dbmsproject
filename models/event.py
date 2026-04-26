"""
models/event.py — Event Model
-------------------------------
Handles all database operations for events:
  - CRUD (Create, Read, Update, Delete)
  - Listing with JOIN to faculty
  - Searching/filtering
  - Participation summary via VIEW
"""

from database.db import get_db


class Event:
    """Encapsulates CRUD operations for the EVENT table."""

    @staticmethod
    def create(name, description, date, venue, max_seats, faculty_id):
        """
        INSERT a new event.

        Args:
            name (str): Event name
            description (str): Event description
            date (str): Event date (YYYY-MM-DD)
            venue (str): Event venue
            max_seats (int): Maximum number of seats
            faculty_id (int): Organizing faculty's ID

        Returns:
            int: New Event_ID
        """
        db = get_db()
        cursor = db.execute(
            """INSERT INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, description, date, venue, max_seats, faculty_id)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_all():
        """
        SELECT all events with faculty name and participant count.
        Uses JOIN (EVENT ↔ FACULTY) and subquery for count.

        Returns:
            list[sqlite3.Row]: All events with metadata.
        """
        db = get_db()
        return db.execute("""
            SELECT
                E.Event_ID,
                E.Name,
                E.Description,
                E.Date,
                E.Venue,
                E.Max_Seats,
                E.Faculty_ID,
                COALESCE(F.Name, 'Unassigned') AS Faculty_Name,
                (SELECT COUNT(*) FROM REGISTRATION R WHERE R.Event_ID = E.Event_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            ORDER BY E.Date DESC
        """).fetchall()

    @staticmethod
    def find_by_id(event_id):
        """
        SELECT a single event by ID with faculty name and participant count.
        Uses JOIN query.
        """
        db = get_db()
        return db.execute("""
            SELECT
                E.Event_ID,
                E.Name,
                E.Description,
                E.Date,
                E.Venue,
                E.Max_Seats,
                E.Faculty_ID,
                COALESCE(F.Name, 'Unassigned') AS Faculty_Name,
                (SELECT COUNT(*) FROM REGISTRATION R WHERE R.Event_ID = E.Event_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            WHERE E.Event_ID = ?
        """, (event_id,)).fetchone()

    @staticmethod
    def update(event_id, name, description, date, venue, max_seats):
        """
        UPDATE an existing event.

        Args:
            event_id (int): Event to update
            name, description, date, venue, max_seats: New values

        Returns:
            bool: True if a row was updated.
        """
        db = get_db()
        cursor = db.execute(
            """UPDATE EVENT
               SET Name = ?, Description = ?, Date = ?, Venue = ?, Max_Seats = ?
               WHERE Event_ID = ?""",
            (name, description, date, venue, max_seats, event_id)
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def delete(event_id):
        """
        DELETE an event by ID.
        Cascading delete removes all related registrations (per FK constraint).

        Args:
            event_id (int): Event to delete

        Returns:
            bool: True if a row was deleted.
        """
        db = get_db()
        cursor = db.execute("DELETE FROM EVENT WHERE Event_ID = ?", (event_id,))
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def search(query):
        """
        Search events by name or venue (partial match).

        Args:
            query (str): Search term

        Returns:
            list[sqlite3.Row]: Matching events.
        """
        db = get_db()
        search_term = f"%{query}%"
        return db.execute("""
            SELECT
                E.Event_ID,
                E.Name,
                E.Description,
                E.Date,
                E.Venue,
                E.Max_Seats,
                COALESCE(F.Name, 'Unassigned') AS Faculty_Name,
                (SELECT COUNT(*) FROM REGISTRATION R WHERE R.Event_ID = E.Event_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            WHERE E.Name LIKE ? OR E.Venue LIKE ? OR E.Description LIKE ?
            ORDER BY E.Date ASC
        """, (search_term, search_term, search_term)).fetchall()

    @staticmethod
    def get_participation_summary():
        """
        SELECT from the vw_event_participation VIEW.
        Demonstrates usage of a database VIEW with JOIN + GROUP BY.

        Returns:
            list[sqlite3.Row]: Participation summary for all events.
        """
        db = get_db()
        return db.execute(
            "SELECT * FROM vw_event_participation ORDER BY Participant_Count DESC"
        ).fetchall()

    @staticmethod
    def get_events_by_faculty(faculty_id):
        """
        SELECT all events organized by a specific faculty member.
        """
        db = get_db()
        return db.execute("""
            SELECT
                E.Event_ID,
                E.Name,
                E.Description,
                E.Date,
                E.Venue,
                E.Max_Seats,
                (SELECT COUNT(*) FROM REGISTRATION R WHERE R.Event_ID = E.Event_ID) AS Participant_Count
            FROM EVENT E
            WHERE E.Faculty_ID = ?
            ORDER BY E.Date ASC
        """, (faculty_id,)).fetchall()
