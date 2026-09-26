"""
Escalation logic — marks complaint as Escalated in the database and notifies admin.
Works directly with inframind.db (SQLite), matching Member 2's schema.
"""

import sqlite3
from datetime import datetime
from automation.notifications import notify_escalation


def get_db():
    conn = sqlite3.connect("inframind.db")
    conn.row_factory = sqlite3.Row
    return conn


def escalate_complaint(complaint_id: int, admin_email: str):
    """
    Marks the complaint as Escalated in the database (only if not already)
    and sends an email notification to admin.
    """
    conn = get_db()

    complaint = conn.execute(
        "SELECT * FROM complaints WHERE id = ?", (complaint_id,)
    ).fetchone()

    if complaint is None:
        conn.close()
        return None

    # Skip if already escalated
    if complaint["status"] == "Escalated":
        conn.close()
        return dict(complaint)

    now = datetime.now().isoformat()

    conn.execute(
        """
        UPDATE complaints
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        ("Escalated", now, complaint_id)
    )
    conn.commit()

    updated_complaint = conn.execute(
        "SELECT * FROM complaints WHERE id = ?", (complaint_id,)
    ).fetchone()

    conn.close()

    # Send email notification
    notify_escalation(admin_email, dict(updated_complaint))

    return dict(updated_complaint)
