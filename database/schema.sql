-- ============================================================
-- Smart College Event Management System — MySQL Database Schema
-- ============================================================
-- Database Engine: MySQL 8.0+ (InnoDB)
-- Normalization: BCNF (Boyce-Codd Normal Form)
--
-- Why MySQL over SQLite?
--   1. MySQL is a full-featured RDBMS with client-server architecture
--   2. InnoDB engine provides ACID-compliant transactions
--   3. Native support for FOREIGN KEY constraints with ON DELETE/UPDATE
--   4. Built-in support for TRIGGERS, VIEWS, STORED PROCEDURES
--   5. Better concurrency control with row-level locking
--   6. Scalable for multi-user production environments
--
-- BCNF Justification:
--   Each table is in BCNF because:
--   1. Every determinant is a candidate key.
--   2. No partial or transitive dependencies exist.
--   3. All non-key attributes are fully functionally dependent
--      on the entire candidate key.
-- ============================================================

-- ============================================================
-- TABLE: STUDENT
-- ============================================================
-- Purpose: Stores student information for authentication & registration
-- Primary Key: Student_ID (AUTO_INCREMENT — MySQL auto-generates unique IDs)
-- Candidate Keys: USN (unique student identifier), Email (unique login)
-- Constraints:
--   - NOT NULL on critical fields ensures data integrity
--   - UNIQUE on USN prevents duplicate university registrations
--   - UNIQUE on Email prevents duplicate login accounts
-- Storage Engine: InnoDB (required for FK constraints & transactions)
-- ============================================================
CREATE TABLE IF NOT EXISTS STUDENT (
    Student_ID  INT             AUTO_INCREMENT,
    USN         VARCHAR(20)     UNIQUE NOT NULL,
    Name        VARCHAR(100)    NOT NULL,
    Dept        VARCHAR(50)     NOT NULL DEFAULT 'General',
    Email       VARCHAR(100)    UNIQUE NOT NULL,
    Password    VARCHAR(255)    NOT NULL,
    PRIMARY KEY (Student_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: FACULTY
-- ============================================================
-- Purpose: Stores faculty/admin users who organize events
-- Primary Key: Faculty_ID (AUTO_INCREMENT)
-- Candidate Key: Email (unique login credential)
-- Functional Dependencies:
--   Faculty_ID → Name, Dept, Email, Password (full FD on PK)
--   Email → Faculty_ID, Name, Dept, Password (Email is candidate key)
-- ============================================================
CREATE TABLE IF NOT EXISTS FACULTY (
    Faculty_ID  INT             AUTO_INCREMENT,
    Name        VARCHAR(100)    NOT NULL,
    Dept        VARCHAR(50)     NOT NULL DEFAULT 'General',
    Email       VARCHAR(100)    UNIQUE NOT NULL,
    Password    VARCHAR(255)    NOT NULL,
    PRIMARY KEY (Faculty_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: EVENT
-- ============================================================
-- Purpose: Stores event details; each event is organized by a faculty
-- Primary Key: Event_ID (AUTO_INCREMENT)
-- Foreign Key: Faculty_ID → FACULTY(Faculty_ID)
--   ON DELETE SET NULL  — If faculty is deleted, event remains but
--                         Faculty_ID becomes NULL (preserves event data)
--   ON UPDATE CASCADE   — If Faculty_ID changes, auto-update here
-- ============================================================
CREATE TABLE IF NOT EXISTS EVENT (
    Event_ID    INT             AUTO_INCREMENT,
    Name        VARCHAR(200)    NOT NULL,
    Description TEXT            DEFAULT NULL,
    Date        DATE            NOT NULL,
    Venue       VARCHAR(200)    NOT NULL,
    Max_Seats   INT             DEFAULT 100,
    Faculty_ID  INT             DEFAULT NULL,
    PRIMARY KEY (Event_ID),
    CONSTRAINT fk_event_faculty
        FOREIGN KEY (Faculty_ID) REFERENCES FACULTY(Faculty_ID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: REGISTRATION
-- ============================================================
-- Purpose: Junction/associative table implementing M:N relationship
--          between STUDENT and EVENT (many students ↔ many events)
-- Primary Key: Reg_ID (AUTO_INCREMENT)
-- Foreign Keys:
--   Student_ID → STUDENT(Student_ID) ON DELETE CASCADE
--     (if student is deleted, their registrations are auto-removed)
--   Event_ID → EVENT(Event_ID) ON DELETE CASCADE
--     (if event is deleted, all its registrations are auto-removed)
-- UNIQUE(Student_ID, Event_ID):
--   Prevents duplicate registration (a student can only register once per event)
--   This composite UNIQUE constraint enforces business rule at DB level
-- TIMESTAMP: Uses MySQL's CURRENT_TIMESTAMP for automatic timestamping
-- ============================================================
CREATE TABLE IF NOT EXISTS REGISTRATION (
    Reg_ID      INT         AUTO_INCREMENT,
    Student_ID  INT         NOT NULL,
    Event_ID    INT         NOT NULL,
    Reg_Time    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (Reg_ID),
    CONSTRAINT fk_reg_student
        FOREIGN KEY (Student_ID) REFERENCES STUDENT(Student_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_reg_event
        FOREIGN KEY (Event_ID) REFERENCES EVENT(Event_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE KEY uq_student_event (Student_ID, Event_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- INDEXES
-- ============================================================
-- Purpose: Speed up frequently executed queries
-- MySQL automatically creates indexes on PRIMARY KEY and UNIQUE columns.
-- These additional indexes optimize JOIN and WHERE clause performance.
--
-- B-Tree Index (default in InnoDB):
--   - Efficient for equality (=) and range (<, >, BETWEEN) queries
--   - idx_registration_student: speeds up "find all events for a student"
--   - idx_registration_event: speeds up "find all students for an event"
--   - idx_event_faculty: speeds up faculty dashboard (my events)
--   - idx_event_date: speeds up date-based sorting and filtering
-- ============================================================
CREATE INDEX idx_registration_student ON REGISTRATION(Student_ID);
CREATE INDEX idx_registration_event   ON REGISTRATION(Event_ID);
CREATE INDEX idx_event_faculty        ON EVENT(Faculty_ID);
CREATE INDEX idx_event_date           ON EVENT(Date);

-- ============================================================
-- VIEW: vw_event_participation
-- ============================================================
-- Purpose: Provides a denormalized, read-only summary of events
--          with their participant counts.
--
-- SQL Concepts Demonstrated:
--   - CREATE VIEW: Virtual table based on a SELECT query
--   - LEFT JOIN: Includes events even if they have no faculty/registrations
--   - GROUP BY: Aggregates registration counts per event
--   - COUNT(): Aggregate function to count participants
--   - COALESCE(): Returns first non-NULL value (handles missing faculty)
--
-- Usage: SELECT * FROM vw_event_participation ORDER BY Participant_Count DESC;
-- ============================================================
CREATE OR REPLACE VIEW vw_event_participation AS
SELECT
    E.Event_ID,
    E.Name       AS Event_Name,
    E.Date       AS Event_Date,
    E.Venue,
    E.Max_Seats,
    COALESCE(F.Name, 'Unassigned') AS Faculty_Name,
    COUNT(R.Reg_ID) AS Participant_Count
FROM EVENT E
LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
GROUP BY E.Event_ID, E.Name, E.Date, E.Venue, E.Max_Seats, F.Name;

-- ============================================================
-- TRIGGER: trg_prevent_overbooking
-- ============================================================
-- Purpose: Enforces maximum seat capacity at the database level
--          BEFORE an INSERT on REGISTRATION table.
--
-- MySQL Trigger Concepts:
--   - BEFORE INSERT: Fires before the row is actually inserted
--   - NEW.Event_ID: References the value being inserted
--   - SIGNAL SQLSTATE '45000': MySQL's way to raise a custom error
--     (equivalent to SQLite's RAISE(ABORT, ...))
--   - SET MESSAGE_TEXT: Custom error message sent to the application
--
-- Flow:
--   1. Count current registrations for the target event
--   2. Fetch Max_Seats for that event
--   3. If current_count >= max_seats → SIGNAL error (abort INSERT)
--   4. Otherwise → INSERT proceeds normally
--
-- This ensures data integrity even if the application logic fails
-- ============================================================
DROP TRIGGER IF EXISTS trg_prevent_overbooking;

CREATE TRIGGER trg_prevent_overbooking
BEFORE INSERT ON REGISTRATION
FOR EACH ROW
BEGIN
    DECLARE current_count INT;
    DECLARE max_allowed INT;

    -- Count existing registrations for this event (SELECT with WHERE)
    SELECT COUNT(*) INTO current_count
    FROM REGISTRATION
    WHERE Event_ID = NEW.Event_ID;

    -- Get the maximum seats allowed (SELECT with WHERE)
    SELECT Max_Seats INTO max_allowed
    FROM EVENT
    WHERE Event_ID = NEW.Event_ID;

    -- Check capacity constraint
    IF current_count >= max_allowed THEN
        -- SIGNAL raises a custom MySQL error to abort the transaction
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'EVENT_FULL: This event has reached maximum capacity.';
    END IF;
END;
