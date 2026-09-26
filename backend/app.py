from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

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

    # Temporary AI output
    category = "Lab"
    department = "IT"
    priority = "High"

    status = "Pending"
    now = datetime.now().isoformat()
        # Calculate deadline based on priority
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
    conn.close()

    return jsonify({
    "message": "Complaint created successfully",
    "category": category,
    "department": department,
    "priority": priority,
    "status": status,
    "deadline": deadline
}), 201

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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )