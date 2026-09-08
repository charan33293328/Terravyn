"""
Decision Stability & Hysteresis Management Module.
Prevents rapid toggling and enforces agronomic redistribution cooldown.
"""

from typing import Tuple, List, Optional
from datetime import datetime, timedelta

DEFAULT_COOLDOWN_HOURS = 2.0
MOISTURE_BUFFER_BAND_PCT = 2.0

def check_irrigation_cooldown(
    hours_since_last_irrigation: Optional[float],
    cooldown_hours: float = DEFAULT_COOLDOWN_HOURS
) -> Tuple[bool, Optional[str]]:
    """
    Check if farm is within post-irrigation redistribution cooldown window.
    Returns (in_cooldown: bool, reason: Optional[str])
    """
    if hours_since_last_irrigation is None:
        return False, None

    if hours_since_last_irrigation < cooldown_hours:
        remaining_minutes = int((cooldown_hours - hours_since_last_irrigation) * 60)
        reason = (
            f"Recent irrigation occurred {hours_since_last_irrigation:.1f} hours ago. "
            f"Soil water redistribution cooldown active ({remaining_minutes} min remaining) "
            "to prevent root zone waterlogging."
        )
        return True, reason

    return False, None
