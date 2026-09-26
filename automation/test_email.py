import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from automation.notifications import send_notification

send_notification(
    to_email="apna_hi_email@gmail.com",   # khud ko bhejo test ke liye
    subject="InfraMind Test Email",
    body="Agar ye email tumhe mila, matlab automation module ka email system kaam kar raha hai!"
)
