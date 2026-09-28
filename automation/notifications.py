"""
Notification module: sends professional, letter-style HTML emails via Gmail SMTP.
Credentials are loaded from .env (SENDER_EMAIL, SENDER_PASSWORD).
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

PLATFORM_NAME = "InfraMind"

PRIORITY_COLORS = {
    "Critical": "#b91c1c",
    "High": "#ea580c",
    "Medium": "#ca8a04",
    "Low": "#16a34a",
}


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def format_deadline(value) -> str:
    if not value:
        return "Not set"
    try:
        dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(value)


def build_html(greeting: str, paragraphs: list, complaint: dict,
               banner_color: str = "#1e3a8a", closing_line: str = "") -> str:
    priority = complaint.get("priority") or "N/A"
    badge_color = PRIORITY_COLORS.get(priority, "#475569")

    rows = [
        ("Complaint ID", f"#{complaint.get('id', 'N/A')}"),
        ("Title", complaint.get("title")),
        ("Category", complaint.get("category")),
        ("Department", complaint.get("department")),
        ("Priority", priority),
        ("Status", complaint.get("status")),
        ("Deadline", format_deadline(complaint.get("deadline"))),
    ]
    rows_html = "".join(
        f"""<tr>
              <td style="padding:9px 12px;color:#64748b;font-size:13px;
                         border-bottom:1px solid #e2e8f0;width:32%;">{label}</td>
              <td style="padding:9px 12px;color:#0f172a;font-size:14px;font-weight:600;
                         border-bottom:1px solid #e2e8f0;">{value}</td>
            </tr>"""
        for label, value in rows if value
    )

    paras_html = "".join(
        f"<p style='margin:0 0 14px;color:#334155;font-size:14px;line-height:1.7;'>{p}</p>"
        for p in paragraphs
    )

    description = complaint.get("description", "")
    description_html = f"""
        <p style="margin:18px 0 6px;color:#64748b;font-size:13px;">Complaint Description</p>
        <div style="background:#f8fafc;border-left:4px solid {banner_color};
                    padding:12px 14px;color:#334155;font-size:14px;line-height:1.6;">
            {description}
        </div>""" if description else ""

    closing = (f"<p style='margin:22px 0 0;color:#334155;font-size:14px;'>{closing_line}</p>"
               if closing_line else "")

    return f"""
    <html>
    <body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="background:#ffffff;border-radius:8px;overflow:hidden;
                        box-shadow:0 1px 4px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:{banner_color};padding:20px 28px;">
                <div style="color:#ffffff;font-size:20px;font-weight:700;">{PLATFORM_NAME}</div>
                <div style="color:#cbd5e1;font-size:12px;">
                    Complaint Management &amp; Automation System</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px;">
                <p style="margin:0 0 16px;color:#0f172a;font-size:15px;font-weight:600;">{greeting}</p>
                {paras_html}
                <span style="display:inline-block;background:{badge_color};color:#ffffff;
                             font-size:12px;font-weight:700;padding:4px 12px;
                             border-radius:12px;margin:4px 0 12px;">
                    {priority.upper()} PRIORITY</span>
                <table width="100%" cellpadding="0" cellspacing="0"
                       style="border:1px solid #e2e8f0;border-radius:6px;">
                    {rows_html}
                </table>
                {description_html}
                {closing}
                <p style="margin:22px 0 0;color:#334155;font-size:14px;line-height:1.6;">
                    Warm regards,<br><b>Team {PLATFORM_NAME}</b></p>
              </td>
            </tr>
            <tr>
              <td style="background:#f8fafc;padding:14px 28px;color:#94a3b8;font-size:12px;">
                This is an automated message from {PLATFORM_NAME}. Please do not reply to this email.
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


def build_plain_text(greeting: str, paragraphs: list, complaint: dict,
                     closing_line: str = "") -> str:
    body = "\n\n".join(p.replace("<b>", "").replace("</b>", "") for p in paragraphs)
    return (
        f"{greeting}\n\n{body}\n\n"
        f"Complaint ID : #{complaint.get('id', 'N/A')}\n"
        f"Title        : {complaint.get('title', 'N/A')}\n"
        f"Category     : {complaint.get('category', 'N/A')}\n"
        f"Department   : {complaint.get('department', 'N/A')}\n"
        f"Priority     : {complaint.get('priority', 'N/A')}\n"
        f"Status       : {complaint.get('status', 'N/A')}\n"
        f"Deadline     : {format_deadline(complaint.get('deadline'))}\n\n"
        f"Description:\n{complaint.get('description', '')}\n\n"
        f"{closing_line}\n\n"
        f"Warm regards,\nTeam {PLATFORM_NAME}"
    )


# ---------------------------------------------------------------
# Core sender
# ---------------------------------------------------------------

def send_notification(to_email: str, subject: str, body: str, html_body: str = None):
    """Generic email sender. html_body is optional."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{PLATFORM_NAME} <{SENDER_EMAIL}>"
        msg["To"] = to_email

        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"Notification sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def _send(to_email, subject, greeting, paragraphs, complaint,
          banner_color="#1e3a8a", closing_line=""):
    send_notification(
        to_email,
        subject,
        build_plain_text(greeting, paragraphs, complaint, closing_line),
        build_html(greeting, paragraphs, complaint, banner_color, closing_line),
    )


# ---------------------------------------------------------------
# Event notifications
# ---------------------------------------------------------------

def notify_complaint_registered(student_email: str, complaint: dict):
    """Confirmation email to the student right after submitting a complaint."""
    dept = complaint.get("department", "the concerned")
    _send(
        student_email,
        f"Complaint #{complaint.get('id')} Registered Successfully",
        "Dear Student,",
        [
            "Thank you for reaching out. Your complaint has been registered successfully.",
            f"It has been sent to the <b>{dept}</b> department, and they must resolve it "
            "before the deadline given below. You can track the progress anytime "
            "on your InfraMind dashboard.",
        ],
        complaint,
        banner_color="#1e3a8a",
        closing_line="We will keep you updated. Thank you for your patience.",
    )


def notify_new_complaint(department_email: str, complaint: dict):
    dept = complaint.get("department", "")
    greeting = f"Dear {dept} Team," if dept else "Dear Team,"
    _send(
        department_email,
        f"New {complaint.get('priority', '')} Priority Complaint - {complaint.get('title', '')}",
        greeting,
        [
            "A new complaint has just been registered and it is assigned to your department.",
            "Please check the details below and resolve it as soon as possible, "
            "before the deadline. If it is not resolved in time, it will go to the HOD/Admin.",
        ],
        complaint,
        closing_line="Thank you for your quick help.",
    )


def notify_status_change(student_email: str, complaint: dict):
    _send(
        student_email,
        f"Complaint #{complaint.get('id')} - Status Updated to {complaint.get('status')}",
        "Dear Student,",
        [
            "There is a new update on your complaint.",
            f"Your complaint status is now <b>{complaint.get('status')}</b>. "
            "You can check the progress anytime on your InfraMind dashboard.",
        ],
        complaint,
        closing_line="Thank you for your patience.",
    )


def notify_deadline_approaching(department_email: str, complaint: dict):
    dept = complaint.get("department", "")
    greeting = f"Dear {dept} Team," if dept else "Dear Team,"
    _send(
        department_email,
        f"Reminder: Complaint #{complaint.get('id')} Deadline Approaching",
        greeting,
        [
            "This is a reminder that the complaint below is still pending and its deadline is close.",
            "Please resolve it as soon as possible so it does not go to the HOD/Admin.",
        ],
        complaint,
        banner_color="#b45309",
        closing_line="Thank you for your quick help.",
    )


def notify_escalation(admin_email: str, complaint: dict):
    _send(
        admin_email,
        f"ESCALATION - Complaint #{complaint.get('id')} Overdue",
        "Dear Admin / HOD,",
        [
            "The complaint below was not resolved before its deadline, "
            "so it has been sent to you automatically.",
            "Please look into it and ask the department to take action as soon as possible.",
        ],
        complaint,
        banner_color="#b91c1c",
        closing_line="Thank you for your urgent attention.",
    )


def notify_resolved(student_email: str, complaint: dict):
    _send(
        student_email,
        f"Complaint #{complaint.get('id')} Resolved",
        "Dear Student,",
        [
            "Good news! Your complaint has been resolved by the department.",
            "If the problem is still there, you can submit a new complaint "
            "or share your feedback on the InfraMind portal.",
        ],
        complaint,
        banner_color="#15803d",
        closing_line="Thank you for helping us make the campus better.",
    )
