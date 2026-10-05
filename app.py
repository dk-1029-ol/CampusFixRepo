"""
CampusFix - app.py
--------------------
This file is the Flask backend that serves all the frontend pages.

All actual data (users, requests) now lives in a real SQLite
database - see database.py for every database function used below
(find_user_by_email, create_request, etc.). This file focuses only
on ROUTES: matching a URL to a function, and deciding what data
that function needs to fetch or save.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

import database as db

app = Flask(__name__)
app.secret_key = "campusfix-dev-secret-key"  # TODO: move to an env variable before real deployment

# Create the database tables (and demo accounts) if they don't exist yet.
# Safe to run every time the app starts.
db.init_db()


# ---------------------------------------------------------------------------
# SERVICES - a fixed list of categories, not something students create,
# so it's kept as a simple Python list rather than a database table.
# "slug" is a plain-lowercase version of the name, made ahead of time here
# in Python, so the templates never need to call a Jinja filter like |lower.
# ---------------------------------------------------------------------------

SERVICES = [
    {"id": 1, "name": "Electrical", "slug": "electrical", "icon": "bi-lightning-charge", "desc": "Fans, switches, wiring, and lighting issues.", "rating": 4.7},
    {"id": 2, "name": "Plumbing", "slug": "plumbing", "icon": "bi-droplet", "desc": "Leaks, taps, drainage, and washroom fittings.", "rating": 4.6},
    {"id": 3, "name": "Cleaning", "slug": "cleaning", "icon": "bi-stars", "desc": "Room, corridor, and common area cleaning.", "rating": 4.8},
    {"id": 4, "name": "IT Support", "slug": "it support", "icon": "bi-laptop", "desc": "Wi-Fi, projectors, lab computers, and network issues.", "rating": 4.5},
    {"id": 5, "name": "Carpentry", "slug": "carpentry", "icon": "bi-hammer", "desc": "Furniture repair, doors, windows, and fittings.", "rating": 4.6},
    {"id": 6, "name": "Maintenance", "slug": "maintenance", "icon": "bi-tools", "desc": "General classroom and hostel maintenance work.", "rating": 4.7},
]

STATUS_LIST = ["Pending", "Accepted", "In Progress", "Completed", "Rejected"]


# ---------------------------------------------------------------------------
# SMALL HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def current_user():
    """Returns the logged-in user's database row, or None if nobody is logged in."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.find_user_by_id(user_id)


def login_required_role(role):
    """
    Very simple check used at the top of protected routes.
    Returns None if the check passes, or a redirect response if it fails.
    """
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if role and user["role"] != role:
        return redirect(url_for("index"))
    return None


def add_display_fields(req):
    """
    Takes ONE request database row and returns a plain dictionary with
    a few extra, ready-made fields added on top. This way, the HTML
    templates never need to do any text formatting themselves (like
    lower-casing or replacing spaces with dashes) - they just print
    these values directly with {{ }}.

    Added fields:
      status_class   -> e.g. "In Progress" becomes "in-progress"
                         (matches our CSS badge class names)
      status_lower   -> e.g. "In Progress" becomes "in progress"
                         (used by the JavaScript status filter dropdowns)
      priority_class -> e.g. "High" becomes "high"
      is_closed      -> True if the request is Completed or Rejected
                         (used to disable the Accept/Reject buttons)
    """
    display = dict(req)  # works for both a plain dict and a database Row
    display["status_class"] = req["status"].lower().replace(" ", "-")
    display["status_lower"] = req["status"].lower()
    display["priority_class"] = req["priority"].lower()
    display["is_closed"] = req["status"] in ["Completed", "Rejected"]
    return display


# ---------------------------------------------------------------------------
# PUBLIC PAGES
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", services=SERVICES, user=current_user())


# ---------------------------------------------------------------------------
# AUTH PAGES
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = db.find_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            if user["role"] == "staff":
                return redirect(url_for("staff_dashboard"))
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid email or password. Please try again."

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        student_id = request.form.get("student_id", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()
        password = request.form.get("password", "")

        if db.find_user_by_email(email):
            error = "An account with this email already exists."
        else:
            password_hash = generate_password_hash(password)
            new_user_id = db.create_user(
                full_name, student_id, email, phone, department, year, password_hash
            )

            # Log the new student in right away and send them to the dashboard
            session["user_id"] = new_user_id
            session["role"] = "student"
            return redirect(url_for("dashboard"))

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# STUDENT PAGES
# ---------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    redirect_response = login_required_role("student")
    if redirect_response:
        return redirect_response

    user = current_user()
    first_name = user["full_name"].split(" ")[0]

    summary = db.count_requests_by_status(user["id"])

    # Show the most recent 5 requests on the dashboard.
    # add_display_fields() adds ready-made fields like status_class,
    # so the template can just print them with no extra logic.
    my_requests = db.get_requests_for_user(user["id"])
    recent_requests = [add_display_fields(r) for r in my_requests[:5]]

    return render_template(
        "dashboard.html", user=user, first_name=first_name, services=SERVICES,
        summary=summary, recent_requests=recent_requests,
    )


@app.route("/services")
def services():
    return render_template("services.html", services=SERVICES, user=current_user())


@app.route("/request-service", methods=["GET", "POST"])
def request_service():
    redirect_response = login_required_role("student")
    if redirect_response:
        return redirect_response

    user = current_user()

    if request.method == "POST":
        service = request.form.get("service", "")
        location = request.form.get("location", "").strip()
        room_number = request.form.get("room_number", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        db.create_request(user["id"], service, location, room_number, description, priority, created_at)
        return redirect(url_for("my_requests"))

    # If the student clicked "Request Service" on a specific service card,
    # the service name is pre-filled through the "?service=" URL parameter
    preselected_service = request.args.get("service", "")
    return render_template(
        "request-service.html", services=SERVICES,
        preselected_service=preselected_service, user=user,
    )


@app.route("/my-requests")
def my_requests():
    redirect_response = login_required_role("student")
    if redirect_response:
        return redirect_response

    user = current_user()
    my_list = db.get_requests_for_user(user["id"])
    my_list = [add_display_fields(r) for r in my_list]
    return render_template("my-requests.html", requests=my_list, user=user)


# ---------------------------------------------------------------------------
# STAFF PAGES
# ---------------------------------------------------------------------------

@app.route("/staff-dashboard")
def staff_dashboard():
    redirect_response = login_required_role("staff")
    if redirect_response:
        return redirect_response

    user = current_user()
    first_name = user["full_name"].split(" ")[0]

    # Rejected requests are intentionally left out here - once staff
    # rejects a request, it disappears from this dashboard. The record
    # still exists in the database, so the student can still see it
    # was rejected on their own "My Requests" page.
    all_requests = db.get_staff_visible_requests()

    summary = db.count_requests_by_status()
    summary["total"] = len(all_requests)  # keep this in sync with the list below (which excludes rejected)

    # Attach the requester's name and the display-ready fields to each
    # request so the staff table can show it with no logic in the template.
    requests_with_names = []
    for r in all_requests:
        requester = db.find_user_by_id(r["user_id"])
        r_display = add_display_fields(r)
        r_display["student_name"] = requester["full_name"] if requester else "Unknown"
        requests_with_names.append(r_display)

    return render_template(
        "staff-dashboard.html", user=user, first_name=first_name,
        summary=summary, requests=requests_with_names,
    )


# ---------------------------------------------------------------------------
# REQUEST DETAILS (shared by both students and staff)
# ---------------------------------------------------------------------------

@app.route("/request/<int:request_id>")
def request_details(request_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    req = db.find_request_by_id(request_id)
    if not req:
        return redirect(url_for("my_requests") if user["role"] == "student" else url_for("staff_dashboard"))

    # A student may only view their own requests
    if user["role"] == "student" and req["user_id"] != user["id"]:
        return redirect(url_for("my_requests"))

    requester = db.find_user_by_id(req["user_id"])
    req_display = add_display_fields(req)

    # Build the status timeline shown to students, so the template just
    # loops over ready-made steps instead of comparing strings itself.
    timeline = []
    for step_label in ["Pending", "Accepted", "In Progress", "Completed"]:
        timeline.append({
            "label": step_label,
            "css_class": step_label.lower().replace(" ", "-"),
            "is_current": step_label == req["status"],
        })

    return render_template(
        "request-details.html", req=req_display, requester=requester,
        user=user, status_list=STATUS_LIST, timeline=timeline,
    )


@app.route("/request/<int:request_id>/update-status", methods=["POST"])
def update_request_status(request_id):
    # Only staff can change a request's status
    redirect_response = login_required_role("staff")
    if redirect_response:
        return redirect_response

    req = db.find_request_by_id(request_id)
    if req:
        # A request that's already Completed or Rejected is "closed" -
        # once it's closed, its status can never be changed again.
        # This check has to live here (not just in the HTML) because a
        # disabled button only stops normal clicks - it doesn't stop
        # someone from re-submitting the same form a second time.
        is_closed = req["status"] in ["Completed", "Rejected"]

        # Priority ordering rule: a High priority request must be
        # handled before any Medium, and Medium before any Low. So
        # before allowing ANY status change here, check whether a
        # more urgent request is still waiting.
        blockers = db.get_higher_priority_active_requests(req["priority"], request_id)

        new_status = request.form.get("status")

        if is_closed:
            pass  # nothing to do - it's already closed
        elif blockers:
            blocker_list = ", ".join(
                "#{} ({})".format(b["id"], b["priority"]) for b in blockers
            )
            flash(
                "Cannot update Request #{} ({} priority) yet - handle these "
                "higher priority request(s) first: {}.".format(
                    request_id, req["priority"], blocker_list
                ),
                "danger",
            )
        elif new_status in STATUS_LIST:
            db.update_request_status(request_id, new_status)

    return redirect(url_for("request_details", request_id=request_id))


if __name__ == "__main__":
    app.run(debug=True)
