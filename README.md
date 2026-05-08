# 🎓 Smart College Event Management System (MySQL Edition)

> A full-stack Flask web application for managing college events, registrations, and participants — powered by **MySQL** as the RDBMS backend.

---

## 📚 DBMS Concepts Demonstrated

This project showcases the following **MySQL/DBMS concepts** that are essential for understanding relational database management systems:

### 1. **Relational Schema Design (BCNF)**
- 4 tables: `STUDENT`, `FACULTY`, `EVENT`, `REGISTRATION`
- All tables are in **Boyce-Codd Normal Form (BCNF)**
- No partial or transitive dependencies exist

### 2. **MySQL Data Types**
- `INT AUTO_INCREMENT` — Auto-generated primary keys
- `VARCHAR(n)` — Variable-length character strings
- `TEXT` — Large text data (event descriptions)
- `DATE` — Date values (YYYY-MM-DD)
- `TIMESTAMP` — Automatic timestamp on INSERT

### 3. **Constraints**
- `PRIMARY KEY` — Unique row identifier
- `FOREIGN KEY` with `ON DELETE CASCADE` / `ON DELETE SET NULL`
- `UNIQUE` — Prevents duplicate USN, Email
- `NOT NULL` — Mandatory fields
- `DEFAULT` — Default values for optional fields

### 4. **CRUD Operations**
- `INSERT INTO` — Create new records (students, events, registrations)
- `SELECT ... FROM ... WHERE` — Read/query records
- `UPDATE ... SET ... WHERE` — Modify existing records
- `DELETE FROM ... WHERE` — Remove records

### 5. **JOIN Queries**
- `INNER JOIN` — Fetch registrations with student details
- `LEFT JOIN` — Fetch events even without assigned faculty
- **Multi-table JOINs** — 3-table joins (REGISTRATION ↔ EVENT ↔ FACULTY)

### 6. **Aggregate Functions & GROUP BY**
- `COUNT()` — Count participants per event
- `GROUP BY` — Group results by event for aggregation
- `COALESCE()` — Handle NULL values in JOINs

### 7. **Subqueries**
- Correlated subqueries for counting registrations per event
- Used in SELECT clause for dynamic participant counts

### 8. **VIEWs**
- `vw_event_participation` — A virtual table combining EVENT, FACULTY, and REGISTRATION data
- Demonstrates `CREATE OR REPLACE VIEW` with JOIN + GROUP BY

### 9. **TRIGGERs**
- `trg_prevent_overbooking` — A `BEFORE INSERT` trigger on REGISTRATION
- Uses `SIGNAL SQLSTATE '45000'` to raise custom errors
- Enforces max seat capacity at the database level

### 10. **TRANSACTIONS (ACID Properties)**
- `START TRANSACTION` → `COMMIT` / `ROLLBACK`
- Used in event registration to ensure atomicity
- **Atomicity**: All-or-nothing operations
- **Consistency**: Valid state transitions
- **Isolation**: No interference between concurrent operations
- **Durability**: Committed data survives crashes

### 11. **INDEXes**
- B-Tree indexes on frequently queried columns
- Speeds up JOIN operations and WHERE clause filtering

### 12. **InnoDB Storage Engine**
- Row-level locking for concurrent access
- Built-in foreign key support
- ACID-compliant transactions

### 13. **SQL Injection Prevention**
- All queries use `%s` parameterized placeholders
- mysql-connector-python handles proper escaping

---

## 🏗️ ER Diagram

```
STUDENT (Student_ID PK, USN UK, Name, Dept, Email UK, Password)
    |
    | 1:M (one student → many registrations)
    ↓
REGISTRATION (Reg_ID PK, Student_ID FK, Event_ID FK, Reg_Time)
    ↑
    | M:1 (many registrations → one event)
    |
EVENT (Event_ID PK, Name, Description, Date, Venue, Max_Seats, Faculty_ID FK)
    ↑
    | M:1 (many events → one faculty)
    |
FACULTY (Faculty_ID PK, Name, Dept, Email UK, Password)
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python Flask |
| Database | **MySQL 8.0+** (InnoDB) |
| MySQL Driver | mysql-connector-python |
| Auth | Session-based + werkzeug PBKDF2 hashing |
| Frontend | Jinja2 Templates + CSS |
| Deployment | Render (Web Service) + Aiven (MySQL) |

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- MySQL 8.0+ (local or cloud)

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/dbmsproject.git
cd dbmsproject

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start local MySQL and create database
mysql -u root -p
# mysql> CREATE DATABASE college_events;
# mysql> EXIT;

# 5. Set environment variables (optional for local)
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=college_events

# 6. Run the application
python app.py
```

### Cloud Deployment (Render + Aiven)

1. **Create MySQL on Aiven** (free tier): https://console.aiven.io/
2. **Deploy to Render**: https://render.com/
3. Set environment variables on Render:
   - `MYSQL_HOST` — Aiven MySQL hostname
   - `MYSQL_PORT` — Aiven MySQL port
   - `MYSQL_USER` — Aiven MySQL username
   - `MYSQL_PASSWORD` — Aiven MySQL password
   - `MYSQL_DATABASE` — `college_events`
   - `SECRET_KEY` — Random secret string

---

## 👤 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Student | aarav@student.edu | password123 |
| Faculty/Admin | ananya@college.edu | password123 |

---

## 📁 Project Structure

```
dbmsproject/
├── app.py                  # Main entry point (MySQL initialization)
├── config.py               # MySQL connection configuration
├── wsgi.py                 # Production WSGI entry point
├── requirements.txt        # Python dependencies
├── build.sh                # Render build script
├── database/
│   ├── db.py               # MySQL connection helper (get_db, close_db, init_db)
│   ├── schema.sql          # MySQL DDL (CREATE TABLE, VIEW, TRIGGER, INDEX)
│   └── seed.sql            # Sample data (INSERT IGNORE)
├── models/
│   ├── student.py          # Student CRUD (MySQL %s queries)
│   ├── faculty.py          # Faculty CRUD
│   ├── event.py            # Event CRUD + JOINs + VIEW queries
│   └── registration.py     # Registration with TRANSACTIONS
├── routes/
│   ├── auth.py             # Login/Register (Student & Faculty)
│   ├── events.py           # Event listing & search
│   ├── registrations.py    # Register/Unregister for events
│   └── admin.py            # Admin dashboard & management
├── templates/              # Jinja2 HTML templates
└── static/                 # CSS, JS, images
```
