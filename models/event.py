"""
models/event.py — Event Model (MySQL with SQLite Fallback)
------------------------------------------------------------
Handles all database operations for events:
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

from database.db import execute_query


class Event:
    """Encapsulates CRUD operations for the EVENT table."""

    @staticmethod
    def create(name, description, date, venue, max_seats, faculty_id):
        """
        INSERT a new event.

        MySQL Query:
            INSERT INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID)
            VALUES (%s, %s, %s, %s, %s, %s)

        Returns:
            int: New Event_ID (AUTO_INCREMENT value)
        """
        result = execute_query(
            """INSERT INTO EVENT (Name, Description, Date, Venue, Max_Seats, Faculty_ID)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, description, date, venue, max_seats, faculty_id),
            commit=True
        )
        return result['lastrowid']

    @staticmethod
    def get_all():
        """
        SELECT all events with faculty name and participant count.

        MySQL Concepts Used:
          - LEFT JOIN: Joins EVENT with FACULTY
          - Correlated Subquery: Counts registrations per event
          - COALESCE(): Returns 'Unassigned' if Faculty Name is NULL
          - ORDER BY DESC: Most recent events first
        """
        return execute_query("""
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
        """, fetch_all=True)

    @staticmethod
    def find_by_id(event_id):
        """
        SELECT a single event by ID with faculty name and participant count.
        Uses LEFT JOIN (EVENT ↔ FACULTY) and correlated subquery.
        """
        return execute_query("""
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
        """, (event_id,), fetch_one=True)

    @staticmethod
    def update(event_id, name, description, date, venue, max_seats):
        """
        UPDATE an existing event.

        MySQL Query:
            UPDATE EVENT SET Name=%s, Description=%s, Date=%s, Venue=%s, Max_Seats=%s
            WHERE Event_ID=%s
        """
        result = execute_query(
            """UPDATE EVENT
               SET Name = %s, Description = %s, Date = %s, Venue = %s, Max_Seats = %s
               WHERE Event_ID = %s""",
            (name, description, date, venue, max_seats, event_id),
            commit=True
        )
        return result['rowcount'] > 0

    @staticmethod
    def delete(event_id):
        """
        DELETE an event by ID.
        ON DELETE CASCADE removes related registrations automatically.
        """
        result = execute_query(
            "DELETE FROM EVENT WHERE Event_ID = %s", (event_id,),
            commit=True
        )
        return result['rowcount'] > 0

    @staticmethod
    def search(query):
        """
        Search events using MySQL LIKE operator with % wildcard.
        """
        search_term = f"%{query}%"
        return execute_query("""
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
        """, (search_term, search_term, search_term), fetch_all=True)

    @staticmethod
    def get_participation_summary():
        """
        SELECT from the vw_event_participation VIEW.
        Demonstrates querying a MySQL VIEW (virtual table).
        """
        return execute_query(
            "SELECT * FROM vw_event_participation ORDER BY Participant_Count DESC",
            fetch_all=True
        )

    @staticmethod
    def get_events_by_faculty(faculty_id):
        """
        SELECT all events organized by a specific faculty member.
        """
        return execute_query("""
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
        """, (faculty_id,), fetch_all=True)
