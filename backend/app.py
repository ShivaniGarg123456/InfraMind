from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import sys
import os
import random
import hashlib

# =========================================================
# PROJECT PATH
# =========================================================

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

# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)

app.secret_key = "inframind-demo-secret-key"

otp_store = {}

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)


# =========================================================
# DATABASE
# =========================================================

def get_db():

    conn = sqlite3.connect("inframind.db")
    conn.row_factory = sqlite3.Row

    return conn

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


def get_department_email(department_name):
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
# =========================================================
# ENSURE USER COLUMNS
# =========================================================

def ensure_user_columns():

    conn = get_db()

    columns = conn.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    existing_columns = {
        column["name"]
        for column in columns
    }

    required_columns = {
        "email": "TEXT",
        "email_verified": "INTEGER DEFAULT 0",
        "otp": "TEXT",
        "otp_expiry": "TEXT"
    }

    for column_name, column_type in required_columns.items():

        if column_name not in existing_columns:

            conn.execute(
                f"""
                ALTER TABLE users
                ADD COLUMN {column_name} {column_type}
                """
            )

    conn.commit()
    conn.close()


ensure_user_columns()


# =========================================================
# HELPER: GET LOGGED-IN USER
# =========================================================

def get_logged_in_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    return user


# =========================================================
# HELPER: GET LOGGED-IN STUDENT
# =========================================================

def get_logged_in_student():

    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db()

    student = conn.execute(
        """
        SELECT
            id,
            username,
            email,
            role,
            student_id
        FROM users
        WHERE id = ?
        AND role = 'student'
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    return student


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return app.send_static_file("index.html")


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/me", methods=["GET"])
def get_current_user():

    user = get_logged_in_user()

    if user is None:

        return jsonify({
            "error": "Please login first"
        }), 401

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"] or user["username"],
        "role": user["role"],
        "student_id": user["student_id"],
        "department": user["department"]
    }), 200


# =========================================================
# SEND OTP
# =========================================================

@app.route("/send-otp", methods=["POST"])
def send_otp():

    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:

        return jsonify({
            "error": "All fields are required"
        }), 400

    email = email.strip().lower()
    name = name.strip()

    if len(password) < 6:

        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    conn = get_db()

    existing_user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE LOWER(email) = ?
        """,
        (email,)
    ).fetchone()

    conn.close()

    if existing_user:

        return jsonify({
            "error": "This email is already registered. You are already registered."
        }), 409

    otp = str(random.randint(100000, 999999))

    otp_expiry = datetime.now() + timedelta(minutes=10)

    password_hash = hashlib.sha256(
        password.encode()
    ).hexdigest()

    otp_store[email] = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "otp": otp,
        "otp_expiry": otp_expiry
    }

    send_notification(
        email,
        "InfraMind - Email Verification OTP",
        f"""
Dear Student,

Your InfraMind email verification OTP is:

{otp}

This OTP is valid for 10 minutes.

Please do not share this OTP with anyone.

Regards,
Team InfraMind
"""
    )

    print("OTP EMAIL SENT TO:", email)
    print("OTP:", otp)

    return jsonify({
        "message": "OTP sent successfully",
        "email": email
    }), 200


# =========================================================
# VERIFY OTP
# =========================================================

@app.route("/verify-otp", methods=["POST"])
def verify_otp():

    data = request.get_json() or {}

    email = data.get("email")
    entered_otp = data.get("otp")

    if not email or not entered_otp:

        return jsonify({
            "error": "Email and OTP are required"
        }), 400

    email = email.strip().lower()
    entered_otp = entered_otp.strip()

    signup_data = otp_store.get(email)

    if signup_data is None:

        return jsonify({
            "error": "OTP not found. Please request a new OTP."
        }), 400

    if datetime.now() > signup_data["otp_expiry"]:

        otp_store.pop(email, None)

        return jsonify({
            "error": "OTP has expired. Please request a new OTP."
        }), 400

    if entered_otp != signup_data["otp"]:

        return jsonify({
            "error": "Invalid OTP. Please enter the correct OTP."
        }), 400

    conn = get_db()

    existing_user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE LOWER(email) = ?
        """,
        (email,)
    ).fetchone()

    if existing_user:

        conn.close()
        otp_store.pop(email, None)

        return jsonify({
            "error": "This email is already registered."
        }), 409

    password_hash = signup_data["password_hash"]

    username = email

    cursor = conn.execute(
        """
        INSERT INTO users
        (
            username,
            email,
            password,
            email_verified,
            otp,
            otp_expiry,
            role,
            student_id,
            department
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            email,
            password_hash,
            1,
            None,
            None,
            "student",
            None,
            None
        )
    )

    user_id = cursor.lastrowid

    student_id = 1000 + user_id

    conn.execute(
        """
        UPDATE users
        SET student_id = ?
        WHERE id = ?
        """,
        (
            student_id,
            user_id
        )
    )

    conn.commit()
    conn.close()

    otp_store.pop(email, None)

    return jsonify({
        "message": "Email verified successfully. Account created.",
        "student_id": student_id,
        "username": username
    }), 201


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:

        return jsonify({
            "error": "Username and password are required"
        }), 400

    username = username.strip().lower()

    password_hash = hashlib.sha256(
        password.encode()
    ).hexdigest()

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE LOWER(username) = ?
        AND password = ?
        """,
        (
            username,
            password_hash
        )
    ).fetchone()

    conn.close()

    if user is None:

        return jsonify({
            "error": "Invalid username or password"
        }), 401

    if user["role"] == "student":

        if user["email_verified"] != 1:

            return jsonify({
                "error": "Please verify your email first."
            }), 403

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["department"] = user["department"]

    return jsonify({
        "message": "Login successful",
        "role": user["role"],
        "student_id": user["student_id"],
        "department": user["department"]
    }), 200


# =========================================================
# OLD SIGNUP ROUTE
# =========================================================

@app.route("/signup", methods=["POST"])
def signup():

    return jsonify({
        "error": "Please use the email OTP signup process."
    }), 400


# =========================================================
# CREATE COMPLAINT
# =========================================================

@app.route("/complaints", methods=["POST"])
def create_complaint():

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first"
        }), 401

    # -----------------------------------------------------
    # Only students
    # -----------------------------------------------------

    if session.get("role") != "student":

        return jsonify({
            "error": "Only students can submit complaints"
        }), 403

    data = request.get_json() or {}

    title = data.get("title")
    description = data.get("description")

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    if not title or not description:

        return jsonify({
            "error": "Title and description are required"
        }), 400

    title = title.strip()
    description = description.strip()

    if not title or not description:

        return jsonify({
            "error": "Title and description cannot be empty"
        }), 400

    # -----------------------------------------------------
    # GET LOGGED-IN STUDENT
    # -----------------------------------------------------

    student = get_logged_in_student()

    if student is None:

        return jsonify({
            "error": "Student account not found. Please login again."
        }), 404

    student_id = student["student_id"]

    if student_id is None:

        return jsonify({
            "error": "Student ID is missing from your account."
        }), 400

    print(
        "CREATING COMPLAINT FOR STUDENT:",
        student_id
    )

    # -----------------------------------------------------
    # AI CLASSIFICATION
    # -----------------------------------------------------

    ai_result = classify_complaint(description)

    category = ai_result["category"]
    department = ai_result["department"]
    priority = ai_result["priority"]

    status = "Pending"

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    created_at = datetime.now()

    now = created_at.isoformat()

    # -----------------------------------------------------
    # DEADLINE
    # -----------------------------------------------------

    deadline = calculate_deadline(
        priority,
        created_at
    ).isoformat()

    # -----------------------------------------------------
    # SAVE COMPLAINT
    # -----------------------------------------------------

    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO complaints
        (
            student_id,
            title,
            description,
            category,
            department,
            priority,
            status,
            deadline,
            created_at,
            updated_at
        )
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

    new_id = cursor.lastrowid

    conn.commit()
    conn.close()

    complaint_info = {
        "id": new_id,
        "student_name": student["username"],
        "title": title,
        "description": description,
        "category": category,
        "department": department,
        "priority": priority,
        "deadline": deadline,
        "status": status,
    }

    # Department ko mail
    notify_new_complaint(get_department_email(department), complaint_info)

    # Student ko confirmation
    if student["email"]:
        notify_complaint_registered(student["email"], complaint_info)

    return jsonify({
        "message": "Complaint created successfully",
        "complaint_id": new_id,
        "student_id": student_id,
        "category": category,
        "department": department,
        "priority": priority,
        "status": status,
        "deadline": deadline
    }), 201
# =========================================================
# STUDENT ANALYTICS
# =========================================================

@app.route("/student-analytics", methods=["GET"])
def student_analytics():

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first"
        }), 401

    if session.get("role") != "student":

        return jsonify({
            "error": "Access denied"
        }), 403

    student = get_logged_in_student()

    if student is None:

        return jsonify({
            "error": "Student account not found"
        }), 404

    student_id = student["student_id"]

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

        "pending": sum(
            1 for c in complaints
            if c["status"] == "Pending"
        ),

        "in_progress": sum(
            1 for c in complaints
            if c["status"] == "In Progress"
        ),

        "resolved": sum(
            1 for c in complaints
            if c["status"] == "Resolved"
        )
    })


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics", methods=["GET"])
def analytics():

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first"
        }), 401

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    if session.get("role") == "student":

        student = get_logged_in_student()

        if student is None:

            return jsonify({
                "error": "Student account not found"
            }), 404

        student_id = student["student_id"]

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

            "pending": sum(
                1 for c in complaints
                if c["status"] == "Pending"
            ),

            "in_progress": sum(
                1 for c in complaints
                if c["status"] == "In Progress"
            ),

            "resolved": sum(
                1 for c in complaints
                if c["status"] == "Resolved"
            )
        })

    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    if session.get("role") != "admin":

        return jsonify({
            "error": "Access denied"
        }), 403

    return jsonify(
        get_analytics_summary()
    )


# =========================================================
# MY COMPLAINTS
# =========================================================

@app.route("/my-complaints", methods=["GET"])
def get_my_complaints():

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first"
        }), 401

    if session.get("role") != "student":

        return jsonify({
            "error": "Access denied"
        }), 403

    student = get_logged_in_student()

    if student is None:

        return jsonify({
            "error": "Student account not found"
        }), 404

    student_id = student["student_id"]

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

    return jsonify([
        dict(row)
        for row in complaints
    ])


# =========================================================
# DEPARTMENT COMPLAINTS
# =========================================================

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

    user = get_logged_in_user()

    if user is None:

        return jsonify({
            "error": "User not found"
        }), 404

    department = user["department"]

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



# =========================================================
# GET ALL COMPLAINTS - ADMIN
# =========================================================

@app.route("/complaints", methods=["GET"])
def get_complaints():

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first"
        }), 401


    # -----------------------------------------------------
    # Only admin can view all complaints
    # -----------------------------------------------------

    if session.get("role") != "admin":

        return jsonify({
            "error": "Access denied"
        }), 403


    conn = get_db()


    # -----------------------------------------------------
    # Get complaints + student email
    # -----------------------------------------------------

    complaints = conn.execute(
        """
        SELECT
            complaints.*,
            users.email AS student_email
        FROM complaints
        LEFT JOIN users
            ON complaints.student_id = users.student_id
        ORDER BY complaints.id DESC
        """
    ).fetchall()


    conn.close()


    return jsonify([
        dict(row)
        for row in complaints
    ])




# =========================================================
# SINGLE COMPLAINT
# =========================================================

@app.route(
    "/complaints/<int:complaint_id>",
    methods=["GET"]
)
def get_complaint(complaint_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first"
        }), 401

    conn = get_db()

    complaint = conn.execute(
        """
        SELECT *
        FROM complaints
        WHERE id = ?
        """,
        (complaint_id,)
    ).fetchone()

    conn.close()

    if complaint is None:

        return jsonify({
            "error": "Complaint not found"
        }), 404

    return jsonify(
        dict(complaint)
    )


# =========================================================
# UPDATE COMPLAINT STATUS
# =========================================================

@app.route(
    "/complaints/<int:complaint_id>/status",
    methods=["PUT"]
)
def update_status(complaint_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first"
        }), 401

    if session.get("role") not in [
        "department",
        "admin"
    ]:

        return jsonify({
            "error": "Access denied"
        }), 403

    data = request.get_json() or {}

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
        """
        SELECT *
        FROM complaints
        WHERE id = ?
        """,
        (complaint_id,)
    ).fetchone()

    if complaint is None:

        conn.close()

        return jsonify({
            "error": "Complaint not found"
        }), 404

    # -----------------------------------------------------
    # Department restriction
    # -----------------------------------------------------

    if session.get("role") == "department":

        user = get_logged_in_user()

        if user is None:

            conn.close()

            return jsonify({
                "error": "User not found"
            }), 404

        if complaint["department"] != user["department"]:

            conn.close()

            return jsonify({
                "error": "You cannot update complaints from another department."
            }), 403

    # -----------------------------------------------------
    # UPDATE STATUS
    # -----------------------------------------------------

        # -----------------------------------------------------
    # UPDATE STATUS
    # -----------------------------------------------------

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

    student_row = conn.execute(
        "SELECT email FROM users WHERE student_id = ?",
        (complaint["student_id"],)
    ).fetchone()

    conn.commit()
    conn.close()

    if student_row and student_row["email"]:
        complaint_info = dict(complaint)
        complaint_info["status"] = new_status
        if new_status == "Resolved":
            notify_resolved(student_row["email"], complaint_info)
        else:
            notify_status_change(student_row["email"], complaint_info)

    return jsonify({
        "message": "Complaint status updated successfully",
        "complaint_id": complaint_id,
        "status": new_status
    })

# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    start_scheduler()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )