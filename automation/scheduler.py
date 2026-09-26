"""
Background scheduler — periodically checks complaints for deadline breaches.
Call start_scheduler() once when the FastAPI app starts.
"""

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from automation.sla_config import STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_OVERDUE, STATUS_RESOLVED
from automation.escalation import escalate_complaint

def get_active_complaints():
    """
    Should return list of complaints with status Pending or In Progress.
    Placeholder — Member 2 (backend) should wire this to actual DB query.
    """
    return []


def check_deadlines():
    complaints = get_active_complaints()
    now = datetime.now()

    for complaint in complaints:
        # Skip if already resolved
        if complaint["status"] == STATUS_RESOLVED:
            continue

        if now > complaint["deadline"]:
            # Step 1: Mark as Overdue if not already
            if complaint["status"] in [STATUS_PENDING, STATUS_IN_PROGRESS]:
                complaint["status"] = STATUS_OVERDUE
                # TODO: Save updated status to DB here

            # Step 2: Escalate if overdue and not yet escalated
            if complaint["status"] == STATUS_OVERDUE and not complaint.get("is_escalated"):
                escalate_complaint(complaint, admin_email="admin@inframind.com")
                # TODO: Save updated complaint back to DB here


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_deadlines, "interval", minutes=15)
    scheduler.start()
    print("Deadline monitoring scheduler started.")
