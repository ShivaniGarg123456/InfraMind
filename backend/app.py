from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import sys
import os

# Allow Python to access the ai folder
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from ai.classifier import classify_complaint
from automation.scheduler import start_scheduler
from automation.analytics import get_analytics_summary
from automation.notifications import notify_new_complaint

DEPARTMENT_EMAILS = {
    "IT": "kashishchauhan616@gmail.com",
    "Maintenance": "24cse2048@mvn.edu.in",
    "Hostel": "24cse2048@mvn.edu.in",
    "Library": "24cse2048@mvn.edu.in",
    "Transport": "24cse2048@mvn.edu.in",
    "Electrical": "24cse2048@mvn.edu.in",
    "Security": "24cse2048@mvn.edu.in",
}

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("inframind.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return "InfraMind Backend Running!"


# CREATE COMPLAINT
@app.route("/complaints", methods=["POST"])
def create_complaint():

    data = request.get_json()

    student_id = data.get("student_id")
    title = data.get("title")
    description = data.get("description")

    # AI complaint classification
    ai_result = classify_complaint(description)

    category = ai_result["category"]
    department = ai_result["department"]
    priority = ai_result["priority"]

    status = "Pending"
    now = datetime.now().isoformat()

    # Calculate deadline based on AI priority
    if priority == "Critical":
        deadline = datetime.now() + timedelta(hours=4)

    elif priority == "High":
        deadline = datetime.now() + timedelta(hours=24)

    elif priority == "Medium":
        deadline = datetime.now() + timedelta(days=2)

    else:
        deadline = datetime.now() + timedelta(days=5)

    deadline = deadline.isoformat()

    conn = get_db()

    conn.execute("""
        INSERT INTO complaints
        (student_id, title, description, category, department,
         priority, status, deadline, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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
    ))

    conn.commit()

# Get the newly created complaint's ID
new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

conn.close()

# Send notification to department
department_email = DEPARTMENT_EMAILS.get(department, "24cse2048@mvn.edu.in")

notify_new_complaint(department_email, {
    "id": new_id,
    "title": title,
    "description": description,
    "category": category,
    "priority": priority,
    "deadline": deadline,
    "status": status
})

return jsonify({
    "message": "Complaint created successfully",
    "category": category,
    "department": department,
    "priority": priority,
    "status": status,
    "deadline": deadline
}), 201


@app.route("/analytics", methods=["GET"])
def analytics():
    return jsonify(get_analytics_summary())
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

    # Allowed statuses
    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved",
        "Overdue",
        "Escalated"
    ]

    # Validate status
    if new_status not in allowed_statuses:
        return jsonify({
            "error": "Invalid status",
            "allowed_statuses": allowed_statuses
        }), 400

    conn = get_db()

    # Check if complaint exists
    complaint = conn.execute(
        "SELECT * FROM complaints WHERE id = ?",
        (complaint_id,)
    ).fetchone()

    if complaint is None:
        conn.close()

        return jsonify({
            "error": "Complaint not found"
        }), 404

    # Update status
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

start_scheduler()
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
