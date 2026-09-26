"""
Analytics logic — basic stats for Admin dashboard.
Queries directly from inframind.db (SQLite).
"""

import sqlite3


def get_db():
    conn = sqlite3.connect("inframind.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_analytics_summary() -> dict:
    """
    Returns summary stats dict by querying the complaints table directly.
    """
    conn = get_db()

    all_complaints = conn.execute("SELECT * FROM complaints").fetchall()
    conn.close()

    complaints = [dict(row) for row in all_complaints]

    total = len(complaints)
    pending = sum(1 for c in complaints if c["status"] == "Pending")
    in_progress = sum(1 for c in complaints if c["status"] == "In Progress")
    resolved = sum(1 for c in complaints if c["status"] == "Resolved")
    overdue = sum(1 for c in complaints if c["status"] == "Overdue")
    escalated = sum(1 for c in complaints if c["status"] == "Escalated")

    department_counts = {}
    priority_counts = {}

    for c in complaints:
        dept = c.get("department") or "Unknown"
        priority = c.get("priority") or "Unknown"
        department_counts[dept] = department_counts.get(dept, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "overdue": overdue,
        "escalated": escalated,
        "department_wise": department_counts,
        "priority_wise": priority_counts,
    }
