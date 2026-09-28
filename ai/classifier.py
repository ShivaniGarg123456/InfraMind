"""
InfraMind - AI/NLP Complaint Classifier
Member 3: Shashi

Hybrid Complaint Classification:
1. Rule-based classification for common complaints
2. Gemini AI fallback for unknown complaints

AI Output:
    category
    department
    priority

Priority:
    Critical, High, Medium, Low
"""

import os
import json
from dotenv import load_dotenv
from google import genai


# Load .env from InfraMind root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)


# Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# GEMINI FALLBACK
# ============================================================

def classify_with_gemini(complaint):
    """
    Use Gemini only when rule-based classification
    cannot identify the complaint.
    """

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

Choose a short and meaningful category based on the complaint.

Priority rules:
- Critical: immediate danger such as fire, smoke, gas leak,
  electric shock, flooding, major electrical hazard
- High: serious issues affecting computers, servers, network,
  WiFi, security, exams or major academic operations
- Medium: normal issues such as fan, AC, light, projector,
  water, hostel or academic problems
- Low: minor issues such as cleaning, dustbin, chair, desk,
  furniture or similar non-urgent problems

Do not add explanations.
Return JSON only.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        response_text = response.text.strip()

        # Remove markdown code fences if Gemini adds them
        if response_text.startswith("```"):
            response_text = response_text.replace("```json", "")
            response_text = response_text.replace("```", "")
            response_text = response_text.strip()

        result = json.loads(response_text)

        # Make sure required keys exist
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

        # Safe fallback
        return {
            "category": "Other",
            "department": "Admin",
            "priority": "Low"
        }


# ============================================================
# MAIN CLASSIFIER
# ============================================================

def classify_complaint(complaint):
    """
    Hybrid complaint classifier.

    First tries rule-based classification.
    If no rule matches, uses Gemini.
    """

    if not complaint:
        return {
            "category": "Other",
            "department": "Admin",
            "priority": "Low"
        }

    text = complaint.lower().strip()

    # ========================================================
    # CRITICAL
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

    if any(keyword in text for keyword in critical_keywords):

        if "gas leak" in text or "gas leakage" in text:
            return {
                "category": "Gas Leak",
                "department": "Maintenance",
                "priority": "Critical"
            }

        elif "flood" in text or "flooding" in text:
            return {
                "category": "Water/Flood",
                "department": "Maintenance",
                "priority": "Critical"
            }

        elif "fire" in text or "smoke" in text:
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
    # HIGH - IT / LAB
    # ========================================================

    if any(keyword in text for keyword in [
        "computer",
        "computers",
        "pc",
        "desktop",
        "laptop",
        "server"
    ]):
        return {
            "category": "Lab",
            "department": "IT",
            "priority": "High"
        }

    # ========================================================
    # HIGH - NETWORK
    # ========================================================

    if any(keyword in text for keyword in [
        "wifi",
        "wi-fi",
        "internet",
        "network",
        "router",
        "connection"
    ]):
        return {
            "category": "Network",
            "department": "IT",
            "priority": "High"
        }

    # ========================================================
    # HIGH - SECURITY
    # ========================================================

    if any(keyword in text for keyword in [
        "security",
        "security guard",
        "theft",
        "stolen",
        "cctv",
        "camera"
    ]):
        return {
            "category": "Security",
            "department": "Security",
            "priority": "High"
        }

    # ========================================================
    # HIGH - EXAM
    # ========================================================

    if any(keyword in text for keyword in [
        "exam",
        "examination",
        "question paper",
        "admit card",
        "hall ticket"
    ]):
        return {
            "category": "Exam",
            "department": "Academic",
            "priority": "High"
        }

    # ========================================================
    # MEDIUM - FAN / AC
    # ========================================================

  if any(keyword in text for keyword in [
    "fan",
    "air conditioner",
    "air conditioning"
]) or text == "ac" or " ac " in text:
        return {
            "category": "Cooling",
            "department": "Electrical",
            "priority": "Medium"
        }

    # ========================================================
    # MEDIUM - LIGHT / ELECTRICITY
    # ========================================================

    if any(keyword in text for keyword in [
        "light",
        "bulb",
        "electricity",
        "switch",
        "power"
    ]):
        return {
            "category": "Electrical",
            "department": "Electrical",
            "priority": "Medium"
        }

    # ========================================================
    # MEDIUM - PROJECTOR
    # ========================================================

    if any(keyword in text for keyword in [
        "projector",
        "display"
    ]):
        return {
            "category": "Projector",
            "department": "IT",
            "priority": "Medium"
        }

    # ========================================================
    # MEDIUM - WATER
    # ========================================================

    if any(keyword in text for keyword in [
        "water",
        "tap",
        "drinking water",
        "water cooler"
    ]):
        return {
            "category": "Water",
            "department": "Maintenance",
            "priority": "Medium"
        }

    # ========================================================
    # MEDIUM - HOSTEL
    # ========================================================

    if any(keyword in text for keyword in [
        "hostel room",
        "hostel"
    ]):
        return {
            "category": "Hostel",
            "department": "Hostel",
            "priority": "Medium"
        }

    # ========================================================
    # LOW - CLEANING
    # ========================================================

    if any(keyword in text for keyword in [
        "cleaning",
        "dirty",
        "dust",
        "dustbin",
        "garbage"
    ]):
        return {
            "category": "Cleaning",
            "department": "Maintenance",
            "priority": "Low"
        }

    # ========================================================
    # LOW - FURNITURE
    # ========================================================

    if any(keyword in text for keyword in [
        "chair",
        "desk",
        "table",
        "bench",
        "furniture"
    ]):
        return {
            "category": "Furniture",
            "department": "Maintenance",
            "priority": "Low"
        }

    # ========================================================
    # MEDIUM - ACADEMIC
    # ========================================================

    if any(keyword in text for keyword in [
        "teacher",
        "faculty",
        "class",
        "lecture",
        "attendance",
        "assignment",
        "subject"
    ]):
        return {
            "category": "Academic",
            "department": "Academic",
            "priority": "Medium"
        }

    # ========================================================
    # MEDIUM - ADMINISTRATIVE
    # ========================================================

    if any(keyword in text for keyword in [
        "fee",
        "fees",
        "scholarship",
        "document",
        "certificate",
        "id card",
        "registration",
        "administration",
        "admin"
    ]):
        return {
            "category": "Administrative",
            "department": "Admin",
            "priority": "Medium"
        }

    # ========================================================
    # GEMINI FALLBACK
    # ========================================================

    print("No rule matched. Sending complaint to Gemini...")

    return classify_with_gemini(complaint)


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    test_complaints = [

        # Rule-based examples
        "Five computers in the CSE lab are not working",
        "The college WiFi is not working",
        "There is a fire in the hostel",

        # Gemini fallback examples
        "The biometric machine keeps rejecting my attendance",
        "The drinking water machine makes a strange noise",
        "My campus parking pass is not being accepted"
    ]

    print("\n========== InfraMind AI Complaint Classifier ==========\n")

    for number, complaint in enumerate(test_complaints, start=1):

        print(f"Test {number}")
        print(f"Complaint: {complaint}")

        result = classify_complaint(complaint)

        print(f"AI Output: {result}")
        print("-" * 60)
