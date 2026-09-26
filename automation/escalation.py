"""
Escalation logic — marks complaint as escalated and notifies admin.
"""

from datetime import datetime
from automation.sla_config import STATUS_ESCALATED
from automation.notifications import notify_escalation


def escalate_complaint(complaint: dict, admin_email: str) -> dict:
    """
    complaint: dict with at least 'id', 'title', 'priority', 'is_escalated'
    Marks complaint as escalated (only once) and sends notification.
    """
    if complaint.get("is_escalated"):
        return complaint  # already escalated, don't do it again

    complaint["status"] = STATUS_ESCALATED
    complaint["is_escalated"] = True
    complaint["escalated_at"] = datetime.now()

    notify_escalation(admin_email, complaint)

    return complaint
