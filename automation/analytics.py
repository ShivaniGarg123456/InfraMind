"""
Analytics logic — basic stats for Admin dashboard.
NOTE: Replace placeholder DB calls with real queries from Member 2's DB module.
"""

def get_analytics_summary(all_complaints: list) -> dict:
    """
    all_complaints: list of complaint dicts
    returns summary stats dict
    """
    total = len(all_complaints)
    pending = sum(1 for c in all_complaints if c["status"] == "Pending")
    in_progress = sum(1 for c in all_complaints if c["status"] == "In Progress")
    resolved = sum(1 for c in all_complaints if c["status"] == "Resolved")
    overdue = sum(1 for c in all_complaints if c["status"] == "Overdue")
    escalated = sum(1 for c in all_complaints if c["status"] == "Escalated")

    department_counts = {}
    priority_counts = {}

    for c in all_complaints:
        dept = c.get("department", "Unknown")
        priority = c.get("priority", "Unknown")
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
