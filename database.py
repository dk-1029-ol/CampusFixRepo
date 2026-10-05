"""
CampusFix - database.py
-------------------------
This file contains ALL the SQLite database code for the project.
Keeping it in its own file (instead of mixing it into app.py) means:
  - app.py stays focused on "which URL does what"
  - all the SQL lives in ONE place, easy to find and change

We use Python's built-in `sqlite3` module - no extra installation
needed. The entire database is just one file: campusfix.db, in the
same folder as this script. It's created automatically the first
time the app runs, so nobody on the team needs to set anything up.

If you ever want to start completely fresh (wipe all data), just
delete the campusfix.db file and run the app again - it will
recreate empty tables and the demo accounts automatically.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "campusfix.db")


def get_connection():
    """
    Opens a connection to the campusfix.db file.

    row_factory = sqlite3.Row lets us read columns by NAME, e.g.
    row["email"], instead of only by position, e.g. row[3]. This is
    what lets our templates keep using {{ user.full_name }} style
    code, exactly like they did with the old fake data.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the 'users' and 'requests' tables if they don't already
    exist, and adds two demo accounts + a few sample requests the
    very first time the app is run (so the site isn't empty).

    This function is safe to call every time the app starts -
    "CREATE TABLE IF NOT EXISTS" does nothing if the table is
    already there.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            student_id TEXT,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            department TEXT,
            year TEXT,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            location TEXT NOT NULL,
            room_number TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()

    # Only add demo data the very first time (i.e. if the users table is empty)
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        _seed_demo_data(conn)

    conn.close()


def _seed_demo_data(conn):
    """
    Adds two ready-made accounts (one student, one staff) and a
    few sample requests, purely so the site has something to show
    the first time it's run. The underscore in the name is just a
    Python convention meaning "internal helper, not meant to be
    called from outside this file."
    """
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (role, full_name, student_id, email, phone, department, year, password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "student", "Aditi Sharma", "STU2024001", "student@campusfix.edu",
        "9876543210", "Computer Engineering", "2nd Year",
        generate_password_hash("student123"),
    ))

    cursor.execute("""
        INSERT INTO users (role, full_name, student_id, email, phone, department, year, password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "staff", "Ramesh Kulkarni", "", "staff@campusfix.edu",
        "9876500000", "Maintenance Team", "",
        generate_password_hash("staff123"),
    ))

    conn.commit()

    student_row = cursor.execute(
        "SELECT id FROM users WHERE email = ?", ("student@campusfix.edu",)
    ).fetchone()
    student_id = student_row["id"]

    sample_requests = [
        (student_id, "Electrical", "Hostel Block B", "B-204",
         "Ceiling fan is making a loud noise and wobbling.", "High",
         "In Progress", "2026-09-08 10:30"),
        (student_id, "IT Support", "Academic Block, Room 5", "AB-105",
         "Classroom projector is not turning on.", "Medium",
         "Pending", "2026-09-09 14:15"),
        (student_id, "Plumbing", "Hostel Block B", "B-204",
         "Washroom tap is leaking continuously.", "Low",
         "Completed", "2026-09-05 09:00"),
    ]
    cursor.executemany("""
        INSERT INTO requests (user_id, service, location, room_number, description, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_requests)

    conn.commit()


# ---------------------------------------------------------------------------
# USER-RELATED QUERIES
# ---------------------------------------------------------------------------

def find_user_by_email(email):
    """Returns one user (as a Row) matching this email, or None if not found."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def find_user_by_id(user_id):
    """Returns one user (as a Row) matching this id, or None if not found."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def create_user(full_name, student_id, email, phone, department, year, password_hash):
    """
    Adds a new student account to the database.
    Every account created through the register page is a student -
    staff accounts are only added directly (see _seed_demo_data above).
    Returns the new user's id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (role, full_name, student_id, email, phone, department, year, password)
        VALUES ('student', ?, ?, ?, ?, ?, ?, ?)
    """, (full_name, student_id, email, phone, department, year, password_hash))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


# ---------------------------------------------------------------------------
# REQUEST-RELATED QUERIES
# ---------------------------------------------------------------------------

def find_request_by_id(request_id):
    """Returns one request (as a Row) matching this id, or None if not found."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
    conn.close()
    return row


def get_requests_for_user(user_id):
    """Returns all of one student's requests, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM requests WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_all_requests():
    """Returns every request in the system, newest first (used by staff)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM requests ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_staff_visible_requests():
    """
    Returns every request EXCEPT rejected ones, newest first.

    This is what powers the "reject removes it from the staff
    dashboard" feature: once staff rejects a request, it's simply
    left out of this list. The row still exists in the database
    (with status = 'Rejected'), so the student who raised it can
    still see it was rejected in their own "My Requests" page - we
    are only hiding it from staff's incoming-requests view.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM requests WHERE status != 'Rejected' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


# Higher number = more urgent. Used to compare two priorities against
# each other, since "High" > "Medium" > "Low" isn't something Python
# or SQLite understands on its own.
PRIORITY_RANK = {"Low": 1, "Medium": 2, "High": 3}


def get_higher_priority_active_requests(priority, exclude_id):
    """
    Returns every request that:
      - is still ACTIVE (status is Pending, Accepted, or In Progress -
        not yet Completed or Rejected), and
      - has a HIGHER priority than the one given, and
      - is not the request we're currently trying to update (exclude_id)

    This is what enforces "High priority must be handled before Medium,
    and Medium before Low": before staff is allowed to change a
    request's status, we check whether anything more urgent is still
    waiting. If this list is NOT empty, the update should be blocked.
    """
    my_rank = PRIORITY_RANK.get(priority, 0)

    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM requests
        WHERE status IN ('Pending', 'Accepted', 'In Progress')
          AND id != ?
    """, (exclude_id,)).fetchall()
    conn.close()

    higher_priority_rows = [r for r in rows if PRIORITY_RANK.get(r["priority"], 0) > my_rank]
    # Show the most urgent one first
    higher_priority_rows.sort(key=lambda r: -PRIORITY_RANK.get(r["priority"], 0))
    return higher_priority_rows


def create_request(user_id, service, location, room_number, description, priority, created_at):
    """Adds a new service request, always starting with status 'Pending'."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO requests (user_id, service, location, room_number, description, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)
    """, (user_id, service, location, room_number, description, priority, created_at))
    conn.commit()
    conn.close()


def update_request_status(request_id, new_status):
    """Changes one request's status (used by staff: Accept / Reject / etc.)."""
    conn = get_connection()
    conn.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, request_id))
    conn.commit()
    conn.close()


def count_requests_by_status(user_id=None):
    """
    Returns a dict like {"total": 3, "pending": 1, "in_progress": 1, "completed": 1}.
    If user_id is given, only counts that student's requests (for the student
    dashboard). If left out, counts every request in the system (for staff).
    """
    conn = get_connection()

    if user_id is not None:
        total = conn.execute(
            "SELECT COUNT(*) FROM requests WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        status_rows = conn.execute(
            "SELECT status, COUNT(*) as how_many FROM requests WHERE user_id = ? GROUP BY status",
            (user_id,),
        ).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        status_rows = conn.execute(
            "SELECT status, COUNT(*) as how_many FROM requests GROUP BY status"
        ).fetchall()

    conn.close()

    counts = {"total": total, "pending": 0, "in_progress": 0, "completed": 0}
    for row in status_rows:
        if row["status"] == "Pending":
            counts["pending"] = row["how_many"]
        elif row["status"] == "In Progress":
            counts["in_progress"] = row["how_many"]
        elif row["status"] == "Completed":
            counts["completed"] = row["how_many"]
    return counts
