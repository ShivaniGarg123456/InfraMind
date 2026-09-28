"""
InfraMind - AI/NLP Complaint Classifier
Member 3: Shashi

Hybrid Complaint Classification:
1. Rule-based classification for common complaints
2. Gemini AI fallback for unknown complaints
"""

import os
import json
import re

from dotenv import load_dotenv
from google import genai


# ============================================================
# ENVIRONMENT / GEMINI SETUP
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# KEYWORD MATCHING HELPERS
# ============================================================

def contains_keyword(text, keyword):
    """
    Match a complete word or phrase.

    This prevents:
        "ac" from matching "machine"
    """

    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

    return re.search(pattern, text.lower()) is not None


def contains_any_keyword(text, keywords):
    """Return True if any keyword matches."""

    return any(
        contains_keyword(text, keyword)
        for keyword in keywords
    )


# ============================================================
# GEMINI FALLBACK
# ============================================================

def classify_with_gemini(complaint):

    if client is None:

        print("Gemini API key not found. Using safe default.")

        return {
            "category": "Other",
            "department": "Admin",
            "priority": "Low"
        }

    prompt = f"""
You are the AI complaint classifier for a college administration
system called InfraMind.

Analyze this student complaint:

"{complaint}"

Return ONLY valid JSON.

The JSON must contain exactly these three keys:

{{
    "category": "...",
    "department": "...",
    "priority": "..."
}}

Allowed priority values:

- Critical
- High
- Medium
- Low

Possible departments:

- IT
- Maintenance
- Electrical
- Hostel
- Admin
- Academic
- Security
- Library
- Transport

Choose a short and meaningful category.

Priority rules:

Critical:
- fire
- smoke
- gas leak
- electric shock
- flooding
- major electrical danger

High:
- computers
- servers
- network
- WiFi
- security
- exams
- major academic operations

Medium:
- fan
- AC
- light
- projector
- water
- hostel
- transport
- normal academic problems

Low:
- cleaning
- dustbin
- chair
- desk
- furniture
- other minor non-urgent problems

Do not classify something as Projector just because the word
"display" appears.

For example:
"campus bus tracking display is incorrect"
should be related to Transport.

Return JSON only.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        response_text = response.text.strip()

        if response_text.startswith("```"):

            response_text = response_text.replace(
                "```json",
                ""
            )

            response_text = response_text.replace(
                "```",
                ""
            )

            response_text = response_text.strip()

        result = json.loads(response_text)

        category = result.get("category")
        department = result.get("department")
        priority = result.get("priority")

        allowed_priorities = {
            "Critical",
            "High",
            "Medium",
            "Low"
        }

        allowed_departments = {
            "IT",
            "Maintenance",
            "Electrical",
            "Hostel",
            "Admin",
            "Academic",
            "Security",
            "Library",
            "Transport"
        }

        if not category:
            category = "Other"

        if department not in allowed_departments:
            department = "Admin"

        if priority not in allowed_priorities:
            priority = "Low"

        return {
            "category": category,
            "department": department,
            "priority": priority
        }

    except Exception as error:

        print("Gemini classification failed:", error)

        print(
            "Gemini is temporarily unavailable. "
            "Using safe default classification."
        )

        return {
            "category": "Other",
            "department": "Admin",
            "priority": "Low"
        }


# ============================================================
# MAIN CLASSIFIER
# ============================================================

def classify_complaint(complaint):

    if not complaint:

        return {
            "category": "Other",
            "department": "Admin",
            "priority": "Low"
        }

    text = complaint.lower().strip()


    # ========================================================
    # CRITICAL - SAFETY
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "fire",
            "smoke",
            "sparking",
            "electric shock",
            "gas leak",
            "gas leakage",
            "flood",
            "flooding"
        ]
    ):

        if contains_any_keyword(
            text,
            ["gas leak", "gas leakage"]
        ):

            return {
                "category": "Gas Leak",
                "department": "Maintenance",
                "priority": "Critical"
            }

        if contains_any_keyword(
            text,
            ["flood", "flooding"]
        ):

            return {
                "category": "Water/Flood",
                "department": "Maintenance",
                "priority": "Critical"
            }

        if contains_any_keyword(
            text,
            ["fire", "smoke"]
        ):

            return {
                "category": "Fire/Safety",
                "department": "Security",
                "priority": "Critical"
            }

        return {
            "category": "Electrical Hazard",
            "department": "Electrical",
            "priority": "Critical"
        }


    # ========================================================
    # HIGH - IT / LAB
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "computer",
            "computers",
            "pc",
            "desktop",
            "laptop",
            "server",
            "servers"
        ]
    ):

        return {
            "category": "Lab",
            "department": "IT",
            "priority": "High"
        }


    # ========================================================
    # HIGH - NETWORK
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "wifi",
            "wi-fi",
            "internet",
            "network",
            "router",
            "connection"
        ]
    ):

        return {
            "category": "Network",
            "department": "IT",
            "priority": "High"
        }


    # ========================================================
    # HIGH - SECURITY
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "security",
            "security guard",
            "theft",
            "stolen",
            "cctv",
            "camera"
        ]
    ):

        return {
            "category": "Security",
            "department": "Security",
            "priority": "High"
        }


    # ========================================================
    # HIGH - EXAM
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "exam",
            "examination",
            "question paper",
            "admit card",
            "hall ticket"
        ]
    ):

        return {
            "category": "Exam",
            "department": "Academic",
            "priority": "High"
        }


    # ========================================================
    # MEDIUM - FAN / AC
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "fan",
            "air conditioner",
            "air conditioning",
            "ac"
        ]
    ):

        return {
            "category": "Cooling",
            "department": "Electrical",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - LIGHT / ELECTRICITY
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "light",
            "bulb",
            "electricity",
            "switch",
            "power"
        ]
    ):

        return {
            "category": "Electrical",
            "department": "Electrical",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - PROJECTOR
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "projector",
            "projector screen",
            "classroom projector"
        ]
    ):

        return {
            "category": "Projector",
            "department": "IT",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - WATER
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "water",
            "tap",
            "drinking water",
            "water cooler"
        ]
    ):

        return {
            "category": "Water",
            "department": "Maintenance",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - HOSTEL
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "hostel room",
            "hostel"
        ]
    ):

        return {
            "category": "Hostel",
            "department": "Hostel",
            "priority": "Medium"
        }


    # ========================================================
    # LOW - CLEANING
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "cleaning",
            "dirty",
            "dust",
            "dustbin",
            "garbage"
        ]
    ):

        return {
            "category": "Cleaning",
            "department": "Maintenance",
            "priority": "Low"
        }


    # ========================================================
    # LOW - FURNITURE
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "chair",
            "desk",
            "table",
            "bench",
            "furniture"
        ]
    ):

        return {
            "category": "Furniture",
            "department": "Maintenance",
            "priority": "Low"
        }


    # ========================================================
    # MEDIUM - BIOMETRIC / ATTENDANCE
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "biometric",
            "fingerprint scanner",
            "fingerprint",
            "attendance machine",
            "attendance scanner"
        ]
    ):

        return {
            "category": "Attendance",
            "department": "Academic",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - ACADEMIC
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "teacher",
            "faculty",
            "class",
            "lecture",
            "attendance",
            "assignment",
            "subject"
        ]
    ):

        return {
            "category": "Academic",
            "department": "Academic",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - ADMINISTRATIVE
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "fee",
            "fees",
            "scholarship",
            "document",
            "certificate",
            "id card",
            "registration",
            "administration",
            "admin"
        ]
    ):

        return {
            "category": "Administrative",
            "department": "Admin",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - TRANSPORT
    # ========================================================

    if contains_any_keyword(
        text,
        [
            "bus",
            "campus bus",
            "transport",
            "shuttle",
            "bus pass",
            "parking",
            "parking pass",
            "vehicle"
        ]
    ):

        return {
            "category": "Transport",
            "department": "Transport",
            "priority": "Medium"
        }


    # ========================================================
    # GEMINI FALLBACK
    # ========================================================

    print(
        "No rule matched. Sending complaint to Gemini..."
    )

    return classify_with_gemini(complaint)


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    test_complaints = [

        "Five computers in the CSE lab are not working",

        "The college WiFi is not working",

        "There is a fire in the hostel",

        "The classroom AC is not working",

        "The classroom fan is broken",

        "The classroom is very dirty",

        "The biometric machine keeps rejecting my attendance",

        "My parking pass is not being accepted at the campus gate",

        "The campus bus tracking display is showing incorrect information",

        "The biometric scanner refuses to recognize my fingerprint",

        "The library book return machine is not accepting books"
    ]

    print(
        "\n========== InfraMind AI Complaint Classifier ==========\n"
    )

    for number, complaint in enumerate(
        test_complaints,
        start=1
    ):

        print(f"Test {number}")

        print(f"Complaint: {complaint}")

        result = classify_complaint(complaint)

        print(f"AI Output: {result}")

        print("-" * 60)