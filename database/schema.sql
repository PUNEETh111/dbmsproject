-- ============================================================
-- Smart College Event Management System — Database Schema
-- ============================================================
-- Database: SQLite 3
-- Normalization: BCNF (Boyce-Codd Normal Form)
-- 
-- Each table is in BCNF because:
--   1. Every determinant is a candidate key.
--   2. No partial or transitive dependencies exist.
-- ============================================================

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- ============================================================
-- TABLE: STUDENT
-- Stores student information.
-- PK: Student_ID (auto-increment)
-- UNIQUE: USN (University Seat Number — primary identity)
-- UNIQUE: Email (prevents duplicate accounts)
-- ============================================================
CREATE TABLE IF NOT EXISTS STUDENT (
    Student_ID  INTEGER PRIMARY KEY AUTOINCREMENT,
    USN         TEXT    UNIQUE NOT NULL,
    Name        TEXT    NOT NULL,
    Dept        TEXT    NOT NULL DEFAULT 'General',
    Email       TEXT    UNIQUE NOT NULL,
    Password    TEXT    NOT NULL
);

-- ============================================================
-- TABLE: FACULTY
-- Stores faculty/admin information.
-- PK: Faculty_ID (auto-increment)
-- ============================================================
CREATE TABLE IF NOT EXISTS FACULTY (
    Faculty_ID  INTEGER PRIMARY KEY AUTOINCREMENT,
    Name        TEXT    NOT NULL,
    Dept        TEXT    NOT NULL DEFAULT 'General',
    Email       TEXT    UNIQUE NOT NULL,
    Password    TEXT    NOT NULL
);

-- ============================================================
-- TABLE: EVENT
-- Stores event details. Each event is organized by a faculty member.
-- PK: Event_ID (auto-increment)
-- FK: Faculty_ID → FACULTY(Faculty_ID)
--     ON DELETE SET NULL — if faculty is deleted, event remains
-- ============================================================
CREATE TABLE IF NOT EXISTS EVENT (
    Event_ID    INTEGER PRIMARY KEY AUTOINCREMENT,
    Name        TEXT    NOT NULL,
    Description TEXT    DEFAULT '',
    Date        TEXT    NOT NULL,
    Venue       TEXT    NOT NULL,
    Max_Seats   INTEGER DEFAULT 100,
    Faculty_ID  INTEGER,
    FOREIGN KEY (Faculty_ID) REFERENCES FACULTY(Faculty_ID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- ============================================================
-- TABLE: REGISTRATION
-- Junction table linking students to events they register for.
-- PK: Reg_ID (auto-increment)
-- FK: Student_ID → STUDENT(Student_ID)
--     ON DELETE CASCADE — if student is deleted, remove registrations
-- FK: Event_ID → EVENT(Event_ID)
--     ON DELETE CASCADE — if event is deleted, remove registrations
-- UNIQUE(Student_ID, Event_ID) — prevents duplicate registration
-- ============================================================
CREATE TABLE IF NOT EXISTS REGISTRATION (
    Reg_ID      INTEGER PRIMARY KEY AUTOINCREMENT,
    Student_ID  INTEGER NOT NULL,
    Event_ID    INTEGER NOT NULL,
    Timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Student_ID) REFERENCES STUDENT(Student_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Event_ID) REFERENCES EVENT(Event_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE(Student_ID, Event_ID)
);

-- ============================================================
-- INDEX: Speed up common queries
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_registration_student ON REGISTRATION(Student_ID);
CREATE INDEX IF NOT EXISTS idx_registration_event   ON REGISTRATION(Event_ID);
CREATE INDEX IF NOT EXISTS idx_event_faculty        ON EVENT(Faculty_ID);
CREATE INDEX IF NOT EXISTS idx_event_date           ON EVENT(Date);

-- ============================================================
-- VIEW: Event Participation Summary
-- Shows each event with participant count — uses JOIN + GROUP BY
-- ============================================================
CREATE VIEW IF NOT EXISTS vw_event_participation AS
SELECT
    E.Event_ID,
    E.Name       AS Event_Name,
    E.Date       AS Event_Date,
    E.Venue,
    E.Max_Seats,
    F.Name       AS Faculty_Name,
    COUNT(R.Reg_ID) AS Participant_Count
FROM EVENT E
LEFT JOIN FACULTY F ON E.Faculty_ID = F.Faculty_ID
LEFT JOIN REGISTRATION R ON E.Event_ID = R.Event_ID
GROUP BY E.Event_ID;

-- ============================================================
-- TRIGGER: Prevent Overbooking
-- Before inserting a registration, check if the event is full.
-- If current registrations >= Max_Seats, abort the insert.
-- ============================================================
CREATE TRIGGER IF NOT EXISTS trg_prevent_overbooking
BEFORE INSERT ON REGISTRATION
BEGIN
    SELECT CASE
        WHEN (
            SELECT COUNT(*) FROM REGISTRATION WHERE Event_ID = NEW.Event_ID
        ) >= (
            SELECT Max_Seats FROM EVENT WHERE Event_ID = NEW.Event_ID
        )
        THEN RAISE(ABORT, 'EVENT_FULL: This event has reached maximum capacity.')
    END;
END;
