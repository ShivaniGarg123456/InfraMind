"""
InfraMind - AI/NLP Complaint Classifier

Hybrid Complaint Classification:
1. Rule-based classification for common complaints
2. OpenRouter AI fallback for unknown complaints

AI Output:
- category
- department
- priority
"""

import os
import json
import re
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

load_dotenv(ENV_PATH)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Model can be changed later from .env without changing this code
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# KEYWORD HELPERS
# ============================================================

def contains_keyword(text, keyword):
    """
    Checks whether a complete keyword exists in the complaint.
    Prevents accidental substring matches.
    """
    return bool(
        re.search(
            r"\b" + re.escape(keyword.lower()) + r"\b",
            text.lower()
        )
    )


def contains_any_keyword(text, keywords):
    """
    Returns True if any keyword exists in the complaint.
    """
    return any(contains_keyword(text, keyword) for keyword in keywords)


# ============================================================
# OPENROUTER AI FALLBACK
# ============================================================

def classify_with_openrouter(complaint):
    """
    Uses OpenRouter AI when no rule-based keyword matches.
    """

    # --------------------------------------------------------
    # If API key is missing, use safe default
    # --------------------------------------------------------

    if not OPENROUTER_API_KEY:
        print("WARNING: OPENROUTER_API_KEY not found.")
        return {
            "category": "Other",
            "department": "Admin",
            "priority": "Low"
        }

    prompt = f"""
You are the AI complaint classification system for a college
complaint management platform called InfraMind.

Analyze the following student complaint and classify it.

Complaint:
"{complaint}"

Return ONLY valid JSON.
Do not write explanations.
Do not use Markdown.
Do not add ```json.

The JSON must contain exactly these keys:

{{
    "category": "...",
    "department": "...",
    "priority": "..."
}}

Allowed departments:
- IT
- Maintenance
- Electrical
- Hostel
- Admin
- Academic
- Security

Allowed priorities:
- Critical
- High
- Medium
- Low

Priority guidelines:

Critical:
- Fire
- Smoke
- Gas leak
- Electric shock
- Flooding
- Major electrical danger
- Immediate safety risk

High:
- Computers
- Servers
- Network
- WiFi
- Internet
- Security systems
- CCTV
- Important examination problems
- Major academic operations

Medium:
- Fan
- AC
- Light
- Projector
- Water
- Hostel problems
- Normal academic issues
- Fees or administrative issues

Low:
- Cleaning
- Dustbin
- Dust
- Chair
- Desk
- Furniture
- Minor maintenance issues

Choose the department that is most relevant to the complaint.
"""


    try:

        # ----------------------------------------------------
        # OpenRouter API Request
        # ----------------------------------------------------

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0
        }

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        # Raise error for HTTP errors
        response.raise_for_status()

        data = response.json()

        # ----------------------------------------------------
        # Extract AI response
        # ----------------------------------------------------

        ai_text = data["choices"][0]["message"]["content"].strip()

        # Remove accidental Markdown code fences
        ai_text = re.sub(
            r"^```json\s*",
            "",
            ai_text,
            flags=re.IGNORECASE
        )

        ai_text = re.sub(
            r"^```\s*",
            "",
            ai_text
        )

        ai_text = re.sub(
            r"\s*```$",
            "",
            ai_text
        )

        # Convert JSON text to Python dictionary
        result = json.loads(ai_text)

        # ----------------------------------------------------
        # Allowed values
        # ----------------------------------------------------

        allowed_departments = {
            "IT",
            "Maintenance",
            "Electrical",
            "Hostel",
            "Admin",
            "Academic",
            "Security"
        }

        allowed_priorities = {
            "Critical",
            "High",
            "Medium",
            "Low"
        }

        # ----------------------------------------------------
        # Validate department
        # ----------------------------------------------------

        department = result.get("department", "Admin")

        if department not in allowed_departments:
            department = "Admin"

        # ----------------------------------------------------
        # Validate priority
        # ----------------------------------------------------

        priority = result.get("priority", "Low")

        if priority not in allowed_priorities:
            priority = "Low"

        # ----------------------------------------------------
        # Validate category
        # ----------------------------------------------------

        category = result.get("category", "Other")

        if not category:
            category = "Other"

        # ----------------------------------------------------
        # Final validated result
        # ----------------------------------------------------

        final_result = {
            "category": str(category).strip(),
            "department": department,
            "priority": priority
        }

        print("OpenRouter classification:", final_result)

        return final_result

    except Exception as e:

        # ----------------------------------------------------
        # Safe fallback
        # ----------------------------------------------------

        print("OpenRouter classification failed:", e)

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
    # CRITICAL COMPLAINTS
    # ========================================================

    critical_keywords = [
        "fire",
        "smoke",
        "sparking",
        "electric shock",
        "gas leak",
        "gas leakage",
        "flood",
        "flooding"
    ]

    if contains_any_keyword(text, critical_keywords):

        if contains_any_keyword(text, [
            "gas leak",
            "gas leakage"
        ]):
            return {
                "category": "Gas Leak",
                "department": "Maintenance",
                "priority": "Critical"
            }

        elif contains_any_keyword(text, [
            "flood",
            "flooding"
        ]):
            return {
                "category": "Water/Flood",
                "department": "Maintenance",
                "priority": "Critical"
            }

        elif contains_any_keyword(text, [
            "fire",
            "smoke"
        ]):
            return {
                "category": "Fire/Safety",
                "department": "Security",
                "priority": "Critical"
            }

        else:
            return {
                "category": "Electrical Hazard",
                "department": "Electrical",
                "priority": "Critical"
            }


    # ========================================================
    # HIGH PRIORITY - IT / LAB
    # ========================================================

    high_it_keywords = [
        "computer",
        "computers",
        "pc",
        "desktop",
        "laptop",
        "server"
    ]

    if contains_any_keyword(text, high_it_keywords):
        return {
            "category": "Lab",
            "department": "IT",
            "priority": "High"
        }


    # ========================================================
    # HIGH PRIORITY - NETWORK
    # ========================================================

    high_network_keywords = [
        "wifi",
        "wi-fi",
        "internet",
        "network",
        "router",
        "connection"
    ]

    if contains_any_keyword(text, high_network_keywords):
        return {
            "category": "Network",
            "department": "IT",
            "priority": "High"
        }


    # ========================================================
    # HIGH PRIORITY - SECURITY
    # ========================================================

    high_security_keywords = [
        "security",
        "security guard",
        "theft",
        "stolen",
        "cctv",
        "camera"
    ]

    if contains_any_keyword(text, high_security_keywords):
        return {
            "category": "Security",
            "department": "Security",
            "priority": "High"
        }


    # ========================================================
    # HIGH PRIORITY - EXAM
    # ========================================================

    high_exam_keywords = [
        "exam",
        "examination",
        "question paper",
        "admit card",
        "hall ticket"
    ]

    if contains_any_keyword(text, high_exam_keywords):
        return {
            "category": "Exam",
            "department": "Academic",
            "priority": "High"
        }


    # ========================================================
    # MEDIUM - COOLING
    # ========================================================

    cooling_keywords = [
        "fan",
        "air conditioner",
        "air conditioning",
        "ac"
    ]

    if contains_any_keyword(text, cooling_keywords):
        return {
            "category": "Cooling",
            "department": "Electrical",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - LIGHT / ELECTRICITY
    # ========================================================

    electricity_keywords = [
        "light",
        "bulb",
        "electricity",
        "switch",
        "power"
    ]

    if contains_any_keyword(text, electricity_keywords):
        return {
            "category": "Electrical",
            "department": "Electrical",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - PROJECTOR
    # ========================================================

    projector_keywords = [
        "projector",
        "display"
    ]

    if contains_any_keyword(text, projector_keywords):
        return {
            "category": "Projector",
            "department": "IT",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - WATER
    # ========================================================

    water_keywords = [
        "water",
        "tap",
        "drinking water",
        "water cooler"
    ]

    if contains_any_keyword(text, water_keywords):
        return {
            "category": "Water",
            "department": "Maintenance",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - HOSTEL
    # ========================================================

    hostel_keywords = [
        "hostel room",
        "hostel"
    ]

    if contains_any_keyword(text, hostel_keywords):
        return {
            "category": "Hostel",
            "department": "Hostel",
            "priority": "Medium"
        }


    # ========================================================
    # LOW - CLEANING
    # ========================================================

    cleaning_keywords = [
        "cleaning",
        "dirty",
        "dust",
        "dustbin",
        "garbage"
    ]

    if contains_any_keyword(text, cleaning_keywords):
        return {
            "category": "Cleaning",
            "department": "Maintenance",
            "priority": "Low"
        }


    # ========================================================
    # LOW - FURNITURE
    # ========================================================

    furniture_keywords = [
        "chair",
        "desk",
        "table",
        "bench",
        "furniture"
    ]

    if contains_any_keyword(text, furniture_keywords):
        return {
            "category": "Furniture",
            "department": "Maintenance",
            "priority": "Low"
        }


    # ========================================================
    # MEDIUM - ACADEMIC
    # ========================================================

    academic_keywords = [
        "teacher",
        "faculty",
        "class",
        "lecture",
        "attendance",
        "assignment",
        "subject"
    ]

    if contains_any_keyword(text, academic_keywords):
        return {
            "category": "Academic",
            "department": "Academic",
            "priority": "Medium"
        }


    # ========================================================
    # MEDIUM - ADMINISTRATIVE
    # ========================================================

    admin_keywords = [
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

    if contains_any_keyword(text, admin_keywords):
        return {
            "category": "Administrative",
            "department": "Admin",
            "priority": "Medium"
        }


    # ========================================================
    # NO KEYWORD MATCH
    #
    # Send unknown complaint to OpenRouter
    # ========================================================

    print("No rule-based keyword matched.")
    print("Sending complaint to OpenRouter...")

    return classify_with_openrouter(complaint)


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    test_complaints = [

        # Rule-based tests
        "Five computers in CSE lab are not working.",
        "WiFi is not working in the library.",
        "There is a fire in the laboratory.",
        "The AC in classroom 302 is not working.",
        "The classroom is dirty.",
        "The projector is not working.",

        # OpenRouter fallback tests
        "The biometric machine keeps rejecting valid student entries.",
        "The parking pass scanner is not recognizing student cards.",
        "The campus bus tracking display is showing incorrect information."
    ]


    print("\n==============================")
    print("INFRA MIND CLASSIFIER TEST")
    print("==============================\n")


    for complaint in test_complaints:

        print("Complaint:")
        print(complaint)

        result = classify_complaint(complaint)

        print("Result:")
        print(result)

        print("-" * 60)
