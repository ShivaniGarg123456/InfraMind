import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from automation.notifications import send_notification

send_notification(
    to_email="24cse2048@mvn.edu.in",   # khud ko bhejo test ke liye
    subject="InfraMind Test Email",
    body="Agar ye email tumhe mila, matlab automation module ka email system kaam kar raha hai!"
)
