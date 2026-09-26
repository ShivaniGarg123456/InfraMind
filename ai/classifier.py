"""
InfraMind - AI/NLP Complaint Classifier
Member 3: Shashi

Rule-based complaint classification.

AI Output:
    category
    department
    priority

Priority:
    Critical, High, Medium, Low
"""


def classify_complaint(complaint):
    """Classify an English college complaint."""

    text = complaint.lower().strip()

    # ---------------------------------------------------------
    # CRITICAL
    # ---------------------------------------------------------
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
            category = "Gas Leak"
            department = "Maintenance"

        elif "flood" in text or "flooding" in text:
            category = "Water/Flood"
            department = "Maintenance"

        elif "fire" in text or "smoke" in text:
            category = "Fire/Safety"
            department = "Security"

        else:
            category = "Electrical Hazard"
            department = "Electrical"

        return {
            "category": category,
            "department": department,
            "priority": "Critical"
        }
    # ---------------------------------------------------------
    # HIGH - NETWORK
    # ---------------------------------------------------------
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
    # ---------------------------------------------------------
    # HIGH - IT / LAB
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # HIGH - SECURITY
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # HIGH - EXAM
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # MEDIUM - FAN / AC
    # ---------------------------------------------------------
    if any(keyword in text for keyword in [
        "fan",
        "air conditioner",
        "air conditioning",
        "ac"
    ]):
        return {
            "category": "Cooling",
            "department": "Electrical",
            "priority": "Medium"
        }

    # ---------------------------------------------------------
    # MEDIUM - LIGHT / ELECTRICITY
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # MEDIUM - PROJECTOR
    # ---------------------------------------------------------
    if any(keyword in text for keyword in [
        "projector",
        "display"
    ]):
        return {
            "category": "Projector",
            "department": "IT",
            "priority": "Medium"
        }

    # ---------------------------------------------------------
    # MEDIUM - WATER
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # MEDIUM - HOSTEL
    # ---------------------------------------------------------
    if any(keyword in text for keyword in [
        "hostel room",
        "hostel"
    ]):
        return {
            "category": "Hostel",
            "department": "Hostel",
            "priority": "Medium"
        }

    # ---------------------------------------------------------
    # LOW - CLEANING
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # LOW - FURNITURE
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # MEDIUM - ACADEMIC
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # MEDIUM - ADMINISTRATIVE
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # DEFAULT
    # ---------------------------------------------------------
    return {
        "category": "Other",
        "department": "Admin",
        "priority": "Low"
    }


# =============================================================
# TESTING
# =============================================================

if __name__ == "__main__":

    test_complaints = [
        "Five computers in the CSE lab are not working",
        "The college WiFi is not working",
        "There is a fire in the hostel",
        "The classroom fan is not working",
        "The classroom is very dirty",
        "The exam admit card is not available",
        "The hostel water tap is leaking",
        "The classroom chairs are broken",
        "There is a gas leak in the hostel",
        "My college ID card is not working"
    ]

    print("========== InfraMind AI Complaint Classifier ==========\n")

    for number, complaint in enumerate(test_complaints, start=1):

        result = classify_complaint(complaint)

        print(f"Test {number}")
        print(f"Complaint: {complaint}")
        print(f"AI Output: {result}")
        print("-" * 60)
