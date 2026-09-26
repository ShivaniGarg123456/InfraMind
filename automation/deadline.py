"""
Deadline calculation logic.
Takes priority + created_at time, returns deadline datetime.
"""

from datetime import datetime, timedelta
from automation.sla_config import SLA_HOURS


def calculate_deadline(priority: str, created_at: datetime) -> datetime:
    """
    priority: one of "Critical", "High", "Medium", "Low"
    created_at: datetime when complaint was created
    returns: deadline datetime
    """
    hours = SLA_HOURS.get(priority)
    if hours is None:
        raise ValueError(f"Unknown priority: {priority}")
    return created_at + timedelta(hours=hours)
