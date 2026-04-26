# 🚀 Smart College Event Management System

A production-quality, full-stack web application for managing college events — built with **Python Flask + SQLite** and a **BCNF-normalized database**.

> **DBMS Mini Project** — Demonstrates JOIN, GROUP BY, VIEW, TRIGGER, TRANSACTION, and referential integrity.

---

## 📁 Folder Structure

```
dbmsproject/
├── app.py                          # Main Flask application (entry point)
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
│
├── database/
│   ├── __init__.py
│   ├── db.py                       # Database connection helper
│   ├── schema.sql                  # DDL: Tables, Views, Triggers, Indexes
│   └── seed.sql                    # Sample data (DML)
│
├── models/                         # Data Access Layer (Model in MVC)
│   ├── __init__.py
│   ├── student.py                  # Student CRUD operations
│   ├── faculty.py                  # Faculty CRUD operations
│   ├── event.py                    # Event CRUD + search + VIEW query
│   └── registration.py            # Registration with TRANSACTION
│
├── routes/                         # Controllers (Controller in MVC)
│   ├── __init__.py
│   ├── auth.py                     # Login/Register/Logout routes
│   ├── events.py                   # Event listing & detail routes
│   ├── registrations.py           # Register/Unregister routes
│   └── admin.py                    # Admin panel routes
│
├── templates/                      # Views (View in MVC)
│   ├── base.html                   # Base layout with navbar & footer
│   ├── home.html                   # Landing page with stats
│   ├── login.html                  # Student login
│   ├── register.html               # Student registration
│   ├── admin_login.html            # Faculty login
│   ├── events.html                 # Event listing with search
│   ├── event_detail.html           # Single event detail
│   ├── my_registrations.html       # Student's registered events
│   ├── 404.html                    # Error page
│   └── admin/
│       ├── dashboard.html          # Admin dashboard with VIEW data
│       ├── create_event.html       # Create event form
│       ├── edit_event.html         # Edit event form
│       └── event_registrations.html # Per-event participant list
│
└── static/
    ├── css/
    │   └── style.css               # Complete dark-theme stylesheet
    └── js/
        └── app.js                  # Client-side interactions
```

---

## ⚡ Quick Setup

### Prerequisites
- **Python 3.8** or higher
- **pip** (Python package manager)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/dbmsproject.git
cd dbmsproject

# 2. Create virtual environment & activate
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python3 app.py
```

The app will:
- Auto-create the SQLite database on first run
- Auto-seed sample data (faculty, students, events, registrations)
- Start at **http://127.0.0.1:5000**

### Demo Credentials

| Role    | Email                 | Password     |
|---------|-----------------------|--------------|
| Student | aarav@student.edu     | password123  |
| Student | priya@student.edu     | password123  |
| Faculty | ananya@college.edu    | password123  |
| Faculty | rajesh@college.edu    | password123  |

---

## 🗂️ Database Schema (ER Diagram)

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   STUDENT    │       │   REGISTRATION   │       │    EVENT     │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ Student_ID PK│◄──────│ Student_ID FK    │       │ Event_ID  PK │
│ Name         │       │ Event_ID   FK    │──────►│ Name         │
│ Dept         │       │ Reg_ID     PK    │       │ Description  │
│ Email UNIQUE │       │ Timestamp        │       │ Date         │
└──────────────┘       └──────────────────┘       │ Venue        │
                               UNIQUE             │ Max_Seats    │
                         (Student_ID, Event_ID)    │ Faculty_ID FK│
                                                   └──────┬───────┘
                                                          │
                                                   ┌──────▼───────┐
                                                   │   FACULTY    │
                                                   ├──────────────┤
                                                   │ Faculty_ID PK│
                                                   │ Name         │
                                                   │ Dept         │
                                                   │ Email UNIQUE │
                                                   │ Password     │
                                                   └──────────────┘
```

---

## 🧮 Database Normalization (1NF → BCNF)

### First Normal Form (1NF) ✅
- All attributes contain **atomic (indivisible) values**
- Each row is **uniquely identifiable** via primary keys
- No repeating groups or arrays

### Second Normal Form (2NF) ✅
- Already in 1NF
- **No partial dependencies**: Every non-key attribute depends on the **entire** primary key
- REGISTRATION uses a surrogate key (Reg_ID) with a UNIQUE constraint on (Student_ID, Event_ID)

### Third Normal Form (3NF) ✅
- Already in 2NF
- **No transitive dependencies**: No non-key attribute depends on another non-key attribute
- Example: In EVENT, Venue depends only on Event_ID, not on Faculty_ID

### Boyce-Codd Normal Form (BCNF) ✅
- Already in 3NF
- **Every determinant is a candidate key**
- Each table has exactly one candidate key (the primary key)
- No functional dependency X → Y exists where X is not a superkey

| Table        | Candidate Key | All FDs are from superkeys? |
|:-------------|:--------------|:---------------------------|
| STUDENT      | Student_ID    | ✅ Yes                     |
| FACULTY      | Faculty_ID    | ✅ Yes                     |
| EVENT        | Event_ID      | ✅ Yes                     |
| REGISTRATION | Reg_ID        | ✅ Yes                     |

---

## 🧮 SQL Features Demonstrated

| Feature         | Location                                  |
|:----------------|:------------------------------------------|
| **JOIN**        | `models/event.py` — EVENT ↔ FACULTY       |
| **JOIN**        | `models/registration.py` — REG ↔ STUDENT  |
| **GROUP BY**    | `models/registration.py` — participant counts |
| **VIEW**        | `database/schema.sql` — vw_event_participation |
| **TRIGGER**     | `database/schema.sql` — trg_prevent_overbooking |
| **TRANSACTION** | `models/registration.py` — BEGIN/COMMIT/ROLLBACK |
| **INSERT**      | Student register, event creation           |
| **UPDATE**      | Edit event                                 |
| **DELETE**      | Delete event (cascading)                   |
| **UNIQUE**      | Email, (Student_ID + Event_ID)             |
| **FOREIGN KEY** | ON DELETE CASCADE / SET NULL               |
| **INDEX**       | On Student_ID, Event_ID, Faculty_ID, Date  |

---

## 🎨 Pages & Features

- **Home** — Hero section, animated stats, event cards with capacity bars
- **Events List** — Search/filter, popularity badges, registration status
- **Event Detail** — Full info, capacity visualization, register/unregister
- **My Registrations** — Table of registered events with cancel option
- **Admin Dashboard** — Stats, event management, participation summary (VIEW)
- **Create/Edit Event** — Forms with validation
- **Event Registrations** — Per-event student list for faculty

---

## 🏗️ Architecture (MVC Pattern)

```
┌─────────────────────────────────┐
│         TEMPLATES (View)        │  ← HTML + Jinja2 templates
├─────────────────────────────────┤
│         ROUTES (Controller)     │  ← Flask Blueprints
├─────────────────────────────────┤
│         MODELS (Model)          │  ← Data access + business logic
├─────────────────────────────────┤
│         SQLite DATABASE         │  ← BCNF-normalized schema
└─────────────────────────────────┘
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask 3.1
- **Database**: SQLite 3
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Authentication**: Werkzeug password hashing (PBKDF2-SHA256)
- **Architecture**: MVC (Model-View-Controller)

---

## 📜 License

This project is created for academic purposes (DBMS Mini Project).
