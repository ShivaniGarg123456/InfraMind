from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
from datetime import datetime
import sys
import os
import random
from automation.notifications import send_notification

# Allow Python to access the project folders
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
from automation.notifications import notify_new_complaint, send_notification


DEPARTMENT_EMAILS = {
    "IT": "kashishchauhan616@gmail.com",
    "Maintenance": "24cse2048@mvn.edu.in",
    "Hostel": "24cse2048@mvn.edu.in",
    "Library": "24cse2048@mvn.edu.in",
    "Transport": "24cse2048@mvn.edu.in",
    "Electrical": "24cse2048@mvn.edu.in",
    "Security": "24cse2048@mvn.edu.in",
}


app = Flask(__name__, static_folder="../frontend", static_url_path="")
app.secret_key = "inframind-demo-secret-key"
otp_store = {}

CORS(app, resources={r"/*": {"origins": "*"}})


def get_db():
    conn = sqlite3.connect("inframind.db")
    conn.row_factory = sqlite3.Row
    return conn


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
    import random
    from datetime import datetime, timedelta

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
    conn.execute(
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

    student_id = data.get("student_id")
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
        (student_id, title, description, category, department,
         priority, status, deadline, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
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

    # Notify respective department
    department_email = DEPARTMENT_EMAILS.get(
        department,
        "24cse2048@mvn.edu.in"
    )

    notify_new_complaint(
        department_email,
        {
            "id": new_id,
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "deadline": deadline,
            "status": status
        }
    )

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

    # Student → only their complaints
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

    # Admin → all complaints
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

    return jsonify({
        "message": "Complaint status updated successfully",
        "complaint_id": complaint_id,
        "status": new_status
    })


if __name__ == "__main__":

    start_scheduler()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
