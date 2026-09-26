"""
SLA Configuration — deadline hours based on priority.
Exact priority values used across project: Critical, High, Medium, Low
"""

SLA_HOURS = {
    "Critical": 4,
    "High": 24,
    "Medium": 48,   # 2 days
    "Low": 120      # 5 days
}

# Status values used across the project (common rule)
STATUS_PENDING = "Pending"
STATUS_IN_PROGRESS = "In Progress"
STATUS_RESOLVED = "Resolved"
STATUS_OVERDUE = "Overdue"
STATUS_ESCALATED = "Escalated"
