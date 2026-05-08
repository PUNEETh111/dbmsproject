"""
models/event.py — Event Model (MySQL)
---------------------------------------
Handles all database operations for events using MySQL:
  - CRUD (Create, Read, Update, Delete)
  - Listing with JOIN to faculty table
  - Searching/filtering with LIKE operator
  - Participation summary via MySQL VIEW

MySQL Concepts Demonstrated:
  - Multi-table JOINs (INNER JOIN, LEFT JOIN)
  - Correlated subqueries (SELECT COUNT(*) inside SELECT)
  - Aggregate functions (COUNT)
  - LIKE operator for pattern matching (% wildcard)
  - COALESCE() for NULL handling
  - ORDER BY for result sorting (ASC/DESC)
  - VIEWs for pre-defined complex queries
  - %s parameterized queries for security
"""

from database.db import get_db


class Event:
    """Encapsulates CRUD operations for the EVENT table in MySQL."""

    @staticmethod
    def create(name, description, date, venue, max_seats, faculty_id):
        """
        INSERT a new event into MySQL.

        MySQL Query:
            INSERT INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID)
            VALUES (%s, %s, %s, %s, %s, %s)

        Args:
            name (str): Event name
            description (str): Event description
            date (str): Event date (YYYY-MM-DD format for MySQL DATE type)
            venue (str): Event venue
            max_seats (int): Maximum number of seats
            faculty_id (int): Organizing faculty's ID (FOREIGN KEY)

        Returns:
            int: New Event_ID (AUTO_INCREMENT value)
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, description, date, venue, max_seats, faculty_id)
        )
        db.commit()
        event_id = cursor.lastrowid
        cursor.close()
        return event_id

    @staticmethod
    def get_all():
        """
        SELECT all events with faculty name and participant count.

        MySQL Concepts Used:
          - LEFT JOIN: Joins EVENT with FACULTY (keeps events even without faculty)
          - Correlated Subquery: Counts registrations per event
          - COALESCE(): Returns 'Unassigned' if Faculty Name is NULL
          - ORDER BY DESC: Most recent events first

        MySQL Query:
            SELECT E.*, COALESCE(F.Name, 'Unassigned') AS Faculty_Name,
                   (SELECT COUNT(*) FROM REGISTRATION R WHERE R.Event_ID = E.Event_ID) AS Participant_Count
            FROM EVENT E
            LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
            ORDER BY E.Date DESC

        Returns:
            list[dict]: All events with metadata.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
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
        """)
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def find_by_id(event_id):
        """
        SELECT a single event by ID with faculty name and participant count.

        Uses LEFT JOIN (EVENT ↔ FACULTY) and correlated subquery for count.

        Args:
            event_id (int): Event's primary key

        Returns:
            dict or None
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
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
            WHERE E.Event_ID = %s
        """, (event_id,))
        result = cursor.fetchone()
        cursor.close()
        return result

    @staticmethod
    def update(event_id, name, description, date, venue, max_seats):
        """
        UPDATE an existing event in MySQL.

        MySQL Query:
            UPDATE EVENT
            SET Name = %s, Description = %s, Date = %s, Venue = %s, Max_Seats = %s
            WHERE Event_ID = %s

        Args:
            event_id (int): Event to update
            name, description, date, venue, max_seats: New values

        Returns:
            bool: True if a row was updated (cursor.rowcount > 0).
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """UPDATE EVENT
               SET Name = %s, Description = %s, Date = %s, Venue = %s, Max_Seats = %s
               WHERE Event_ID = %s""",
            (name, description, date, venue, max_seats, event_id)
        )
        db.commit()
        updated = cursor.rowcount > 0
        cursor.close()
        return updated

    @staticmethod
    def delete(event_id):
        """
        DELETE an event by ID from MySQL.

        MySQL Query: DELETE FROM EVENT WHERE Event_ID = %s

        Note: The FOREIGN KEY constraint with ON DELETE CASCADE on REGISTRATION
        table automatically removes all registration rows for this event.
        This is handled by InnoDB at the storage engine level.

        Args:
            event_id (int): Event to delete

        Returns:
            bool: True if a row was deleted.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM EVENT WHERE Event_ID = %s", (event_id,))
        db.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    @staticmethod
    def search(query):
        """
        Search events by name, venue, or description using MySQL LIKE operator.

        MySQL LIKE Operator:
          - % wildcard matches zero or more characters
          - _ wildcard matches exactly one character
          - LIKE '%search%' finds partial matches anywhere in the string

        MySQL Query:
            SELECT ... FROM EVENT E
            LEFT JOIN FACULTY F ON ...
            WHERE E.Name LIKE %s OR E.Venue LIKE %s OR E.Description LIKE %s
            ORDER BY E.Date ASC

        Args:
            query (str): Search term

        Returns:
            list[dict]: Matching events.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        search_term = f"%{query}%"
        cursor.execute("""
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
            WHERE E.Name LIKE %s OR E.Venue LIKE %s OR E.Description LIKE %s
            ORDER BY E.Date ASC
        """, (search_term, search_term, search_term))
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def get_participation_summary():
        """
        SELECT from the vw_event_participation VIEW.

        This demonstrates querying a MySQL VIEW — a virtual table defined by a
        stored SELECT query. The view encapsulates a complex JOIN + GROUP BY
        query so it can be reused with a simple SELECT.

        MySQL Query: SELECT * FROM vw_event_participation ORDER BY Participant_Count DESC

        Returns:
            list[dict]: Participation summary for all events.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM vw_event_participation ORDER BY Participant_Count DESC"
        )
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def get_events_by_faculty(faculty_id):
        """
        SELECT all events organized by a specific faculty member.

        MySQL Query:
            SELECT E.*, (SELECT COUNT(*) FROM REGISTRATION R WHERE R.Event_ID = E.Event_ID)
            FROM EVENT E WHERE E.Faculty_ID = %s ORDER BY E.Date ASC

        Args:
            faculty_id (int): Faculty's primary key (FOREIGN KEY reference)

        Returns:
            list[dict]: Events organized by the specified faculty.
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                E.Event_ID,
                E.Name,
                E.Description,
                E.Date,
                E.Venue,
                E.Max_Seats,
                (SELECT COUNT(*) FROM REGISTRATION R WHERE R.Event_ID = E.Event_ID) AS Participant_Count
            FROM EVENT E
            WHERE E.Faculty_ID = %s
            ORDER BY E.Date ASC
        """, (faculty_id,))
        results = cursor.fetchall()
        cursor.close()
        return results
