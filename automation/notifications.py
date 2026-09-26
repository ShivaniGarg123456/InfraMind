"""
Notification module — sends email notifications for various events.
Uses Gmail SMTP.
"""

import smtplib
from email.mime.text import MIMEText

# TODO: Move these to environment variables (.env) before pushing real credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"   # Use Gmail App Password, not real password


def send_notification(to_email: str, subject: str, body: str):
    """Generic email sender."""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"Notification sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def notify_new_complaint(department_email: str, complaint: dict):
    subject = f"New Complaint #{complaint['id']} - {complaint['category']}"
    body = (
        f"Title: {complaint['title']}\n"
        f"Description: {complaint['description']}\n"
        f"Priority: {complaint['priority']}\n"
        f"Deadline: {complaint['deadline']}\n"
    )
    send_notification(department_email, subject, body)


def notify_status_change(student_email: str, complaint: dict):
    subject = f"Complaint #{complaint['id']} - Status Updated"
    body = f"Your complaint status is now: {complaint['status']}"
    send_notification(student_email, subject, body)


def notify_deadline_approaching(department_email: str, complaint: dict):
    subject = f"⏰ Reminder: Complaint #{complaint['id']} deadline approaching"
    body = f"Complaint '{complaint['title']}' deadline is at {complaint['deadline']}. Please act soon."
    send_notification(department_email, subject, body)


def notify_escalation(admin_email: str, complaint: dict):
    subject = f"⚠️ Complaint #{complaint['id']} ESCALATED"
    body = (
        f"Complaint '{complaint['title']}' has crossed its deadline "
        f"and has been escalated.\nPriority: {complaint['priority']}"
    )
    send_notification(admin_email, subject, body)


def notify_resolved(student_email: str, complaint: dict):
    subject = f"✅ Complaint #{complaint['id']} Resolved"
    body = f"Your complaint '{complaint['title']}' has been marked as Resolved."
    send_notification(student_email, subject, body)
