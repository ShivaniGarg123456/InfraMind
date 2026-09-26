"""
Background scheduler — periodically checks complaints in inframind.db
for deadline breaches, marks them Overdue, then Escalated.
"""

import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from automation.escalation import escalate_complaint
from automation.notifications import notify_deadline_approaching

ADMIN_EMAIL = "24cse2048@mvn.edu.in"  # TODO: replace with real admin email


def get_db():
    conn = sqlite3.connect("inframind.db")
    conn.row_factory = sqlite3.Row
    return conn


def mark_overdue(complaint_id: int):
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE complaints SET status = ?, updated_at = ? WHERE id = ?",
        ("Overdue", now, complaint_id)
    )
    conn.commit()
    conn.close()


def check_deadlines():
    conn = get_db()

    # Only check complaints that are still active (not Resolved/Escalated)
    complaints = conn.execute(
        """
        SELECT * FROM complaints
        WHERE status IN ('Pending', 'In Progress', 'Overdue')
        """
    ).fetchall()

    conn.close()

    now = datetime.now()

    for row in complaints:
        complaint = dict(row)

        if not complaint["deadline"]:
            continue  # skip if deadline missing

        deadline = datetime.fromisoformat(complaint["deadline"])

        if now > deadline:
            if complaint["status"] in ["Pending", "In Progress"]:
                mark_overdue(complaint["id"])
                print(f"Complaint #{complaint['id']} marked Overdue")

            # Escalate (whether it was just marked Overdue or already was)
            escalate_complaint(complaint["id"], ADMIN_EMAIL)
            print(f"Complaint #{complaint['id']} escalated")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_deadlines, "interval", minutes=15)
    scheduler.start()
    print("Deadline monitoring scheduler started.")
