from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
from datetime import datetime
import sys
import os
import random

# Allow Python to access the project folders (must be BEFORE project imports)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from ai.classifier import classify_complaint
from automation.deadline import calculate_deadline
from automation.scheduler import start_scheduler
from automation.analytics import get_analytics_summary
from automation.notifications import (
    send_notification,
    notify_new_complaint,
    notify_complaint_registered,
    notify_status_change,
    notify_resolved,
)


# Fallback emails (used only if department has no email in the users table)
DEPARTMENT_EMAILS = {
    "IT": "kashishchauhan616@gmail.com",
    "Maintenance": "24cse2048@mvn.edu.in",
    "Hostel": "24cse2048@mvn.edu.in",
    "Electrical": "24cse2048@mvn.edu.in",
    "Security": "24cse2048@mvn.edu.in",
    "Academic": "24cse2048@mvn.edu.in",
    "Admin": "24cse2048@mvn.edu.in",
}
DEFAULT_EMAIL = "24cse2048@mvn.edu.in"


app = Flask(__name__, static_folder="../frontend", static_url_path="")
app.secret_key = "inframind-demo-secret-key"
otp_store = {}

CORS(app, resources={r"/*": {"origins": "*"}})


def get_db():
    conn = sqlite3.connect("inframind.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------
# AUTOMATION HELPERS (emails lookup)
# ---------------------------------------------------------------

def ensure_columns():
    """Adds student_name column to complaints if missing, and fixes
    old student users whose student_id is empty."""
    conn = get_db()
    try:
        conn.execute("ALTER TABLE complaints ADD COLUMN student_name TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.execute(
        """
        UPDATE users
        SET student_id = id
        WHERE role = 'student' AND student_id IS NULL
        """
    )
    conn.commit()
    conn.close()


def get_user_email(user_id):
    """Email of the logged-in user (the one used for signup/login)."""
    if not user_id:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["email"] if row and row["email"] else None


def get_student_email_by_student_id(student_id):
    """Email of a student using student_id (used when department updates status)."""
    if not student_id:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT email FROM users WHERE role = 'student' AND student_id = ?",
        (student_id,)
    ).fetchone()
    conn.close()
    return row["email"] if row and row["email"] else None


def get_department_email(department_name):
    """Department email: first from users table (admin-added departments),
    otherwise from the fallback dictionary."""
    conn = get_db()
    row = conn.execute(
        """
        SELECT email FROM users
        WHERE role = 'department' AND department = ?
        AND email IS NOT NULL AND email != ''
        """,
        (department_name,)
    ).fetchone()
    conn.close()

    if row and row["email"]:
        return row["email"]
    return DEPARTMENT_EMAILS.get(department_name, DEFAULT_EMAIL)


# ---------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------

@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/send-otp", methods=["POST"])
def send_otp():

    data = request.get_json()

    email = data.get("email")

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # Store OTP temporarily
    otp_store[email] = otp

    # Send OTP using existing Gmail system
    send_notification(
        email,
        "InfraMind - Email Verification OTP",
        f"""
Dear Student,

Your InfraMind email verification OTP is:

{otp}

This OTP is required to verify your email address.

Please do not share this OTP with anyone.

Regards,
Team InfraMind
"""
    )

    return jsonify({
        "message": "OTP sent successfully"
    })


# LOGIN
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    import hashlib

    password_hash = hashlib.sha256(
        password.encode()
    ).hexdigest()

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        AND password = ?
        """,
        (username, password_hash)
    ).fetchone()

    conn.close()

    if user is None:
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    # Create login session
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["student_id"] = user["student_id"]
    session["department"] = user["department"]

    return jsonify({
        "message": "Login successful",
        "role": user["role"],
        "student_id": user["student_id"],
        "department": user["department"]
    })


# STUDENT SIGNUP
@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({
            "error": "Username, email and password are required"
        }), 400

    import hashlib
    from datetime import timedelta

    password_hash = hashlib.sha256(
        password.encode()
    ).hexdigest()

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # OTP valid for 10 minutes
    otp_expiry = (
        datetime.now() + timedelta(minutes=10)
    ).isoformat()

    conn = get_db()

    # Check username
    existing_user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    if existing_user:
        conn.close()

        return jsonify({
            "error": "Username already exists"
        }), 409

    # Check email
    existing_email = conn.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    if existing_email:
        conn.close()

        return jsonify({
            "error": "Email already registered"
        }), 409

    # Create student account
    cursor = conn.execute(
        """
        INSERT INTO users
        (username, email, password, email_verified,
         otp, otp_expiry, role, student_id, department)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            email,
            password_hash,
            0,
            otp,
            otp_expiry,
            "student",
            None,
            None
        )
    )

    # student_id = user id (so complaints and emails can be linked)
    new_user_id = cursor.lastrowid
    conn.execute(
        "UPDATE users SET student_id = ? WHERE id = ?",
        (new_user_id, new_user_id)
    )

    conn.commit()
    conn.close()

    print("OTP for", email, ":", otp)

    return jsonify({
        "message": "OTP sent to your email",
        "email": email
    }), 201


# CREATE COMPLAINT
@app.route("/complaints", methods=["POST"])
def create_complaint():

    data = request.get_json()

    # Student identity comes from the login session (not from the form).
    # data.get("student_id") is only a fallback for API testing.
    student_id = session.get("student_id") or data.get("student_id")
    student_name = data.get("student_name")
    title = data.get("title")
    description = data.get("description")

    ai_result = classify_complaint(description)

    category = ai_result["category"]
    department = ai_result["department"]
    priority = ai_result["priority"]

    status = "Pending"

    # Create complaint time
    created_at = datetime.now()
    now = created_at.isoformat()

    # Calculate deadline using automation SLA rules
    deadline = calculate_deadline(
        priority,
        created_at
    ).isoformat()

    conn = get_db()

    conn.execute(
        """
        INSERT INTO complaints
        (student_id, student_name, title, description, category, department,
         priority, status, deadline, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            student_name,
            title,
            description,
            category,
            department,
            priority,
            status,
            deadline,
            now,
            now
        )
    )

    conn.commit()

    new_id = conn.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    conn.close()

    complaint_info = {
        "id": new_id,
        "student_name": student_name,
        "title": title,
        "description": description,
        "category": category,
        "department": department,
        "priority": priority,
        "deadline": deadline,
        "status": status
    }

    # 1) Mail to the concerned department
    notify_new_complaint(
        get_department_email(department),
        complaint_info
    )

    # 2) Confirmation mail to the student (login email)
    student_email = get_user_email(session.get("user_id"))
    if not student_email:
        student_email = get_student_email_by_student_id(student_id)

    if student_email:
        notify_complaint_registered(student_email, complaint_info)

    return jsonify({
        "message": "Complaint created successfully",
        "category": category,
        "department": department,
        "priority": priority,
        "status": status,
        "deadline": deadline
    }), 201


# STUDENT ANALYTICS
@app.route("/student-analytics", methods=["GET"])
def student_analytics():

    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    if session.get("role") != "student":
        return jsonify({"error": "Access denied"}), 403

    student_id = session.get("student_id")

    conn = get_db()

    complaints = conn.execute(
        """
        SELECT status
        FROM complaints
        WHERE student_id = ?
        """,
        (student_id,)
    ).fetchall()

    conn.close()

    return jsonify({
        "total": len(complaints),
        "pending": sum(1 for c in complaints if c["status"] == "Pending"),
        "in_progress": sum(1 for c in complaints if c["status"] == "In Progress"),
        "resolved": sum(1 for c in complaints if c["status"] == "Resolved")
    })


# ANALYTICS
@app.route("/analytics", methods=["GET"])
def analytics():
    print("SESSION:", dict(session))

    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    # Student -> only their complaints
    if session.get("role") == "student":

        student_id = session.get("student_id")

        conn = get_db()

        complaints = conn.execute(
            """
            SELECT status
            FROM complaints
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchall()

        conn.close()

        total = len(complaints)
        pending = sum(1 for c in complaints if c["status"] == "Pending")
        in_progress = sum(1 for c in complaints if c["status"] == "In Progress")
        resolved = sum(1 for c in complaints if c["status"] == "Resolved")

        return jsonify({
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved
        })

    # Admin -> all complaints
    return jsonify(get_analytics_summary())


# GET LOGGED-IN STUDENT'S COMPLAINTS
@app.route("/my-complaints", methods=["GET"])
def get_my_complaints():

    # Check if user is logged in
    if "user_id" not in session:
        return jsonify({
            "error": "Please login first"
        }), 401

    # Only students can access this
    if session.get("role") != "student":
        return jsonify({
            "error": "Access denied"
        }), 403

    student_id = session.get("student_id")

    conn = get_db()

    complaints = conn.execute(
        """
        SELECT *
        FROM complaints
        WHERE student_id = ?
        ORDER BY id DESC
        """,
        (student_id,)
    ).fetchall()

    conn.close()

    return jsonify([dict(row) for row in complaints])


# GET DEPARTMENT COMPLAINTS
@app.route("/department-complaints", methods=["GET"])
def get_department_complaints():

    if "user_id" not in session:
        return jsonify({
            "error": "Please login first"
        }), 401

    if session.get("role") != "department":
        return jsonify({
            "error": "Access denied"
        }), 403

    department = session.get("department")

    conn = get_db()

    complaints = conn.execute(
        """
        SELECT *
        FROM complaints
        WHERE department = ?
        ORDER BY id DESC
        """,
        (department,)
    ).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in complaints
    ])


# GET ALL COMPLAINTS
@app.route("/complaints", methods=["GET"])
def get_complaints():

    conn = get_db()

    complaints = conn.execute(
        "SELECT * FROM complaints"
    ).fetchall()

    conn.close()

    return jsonify([dict(row) for row in complaints])


# GET SINGLE COMPLAINT
@app.route("/complaints/<int:complaint_id>", methods=["GET"])
def get_complaint(complaint_id):

    conn = get_db()

    complaint = conn.execute(
        "SELECT * FROM complaints WHERE id = ?",
        (complaint_id,)
    ).fetchone()

    conn.close()

    if complaint is None:
        return jsonify({
            "error": "Complaint not found"
        }), 404

    return jsonify(dict(complaint))


# UPDATE COMPLAINT STATUS
@app.route("/complaints/<int:complaint_id>/status", methods=["PUT"])
def update_status(complaint_id):

    data = request.get_json()
    new_status = data.get("status")

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved",
        "Overdue",
        "Escalated"
    ]

    if new_status not in allowed_statuses:
        return jsonify({
            "error": "Invalid status",
            "allowed_statuses": allowed_statuses
        }), 400

    conn = get_db()

    complaint = conn.execute(
        "SELECT * FROM complaints WHERE id = ?",
        (complaint_id,)
    ).fetchone()

    if complaint is None:
        conn.close()

        return jsonify({
            "error": "Complaint not found"
        }), 404

    conn.execute(
        """
        UPDATE complaints
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            new_status,
            datetime.now().isoformat(),
            complaint_id
        )
    )

    conn.commit()
    conn.close()

    # Mail the student about the status change
    complaint_info = dict(complaint)
    complaint_info["status"] = new_status

    student_email = get_student_email_by_student_id(complaint["student_id"])
    if student_email:
        if new_status == "Resolved":
            notify_resolved(student_email, complaint_info)
        else:
            notify_status_change(student_email, complaint_info)

    return jsonify({
        "message": "Complaint status updated successfully",
        "complaint_id": complaint_id,
        "status": new_status
    })


if __name__ == "__main__":

    ensure_columns()
    start_scheduler()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
