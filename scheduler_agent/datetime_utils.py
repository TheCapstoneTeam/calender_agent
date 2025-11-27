from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

def get_local_timezone():
    """
    Auto-detect the system's local timezone.
    Returns a timezone object (ZoneInfo or datetime.timezone).
    """
    # Get local timezone using datetime
    local_tz = datetime.now().astimezone().tzinfo
    return local_tz


def parse_date(date_str):
    """
    Accepts DD-MM-YYYY or YYYY-MM-DD
    Returns Python datetime.date
    """
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()
    except:
        return datetime.strptime(date_str, "%Y-%m-%d").date()


def parse_time(time_str):
    """
    Accepts:
        "11:15"
        "2hr"
        "2h"
        "30min"
        "1h 30m"
    Returns timedelta OR time object
    """

    time_str = time_str.lower().strip()

    # format like HH:MM
    if ":" in time_str:
        return datetime.strptime(time_str, "%H:%M").time()

    # format like "2hr", "1h", "2hours"
    if "h" in time_str:
        hrs = int(''.join([c for c in time_str if c.isdigit()]))
        return timedelta(hours=hrs)

    # format like "30min", "45m"
    if "m" in time_str:
        mins = int(''.join([c for c in time_str if c.isdigit()]))
        return timedelta(minutes=mins)

    raise ValueError("Invalid time format.")


def to_iso(date_obj=None, time_obj=None, local_tz=None):
    """
    Convert date + time or datetime into ISO string in UTC (RFC3339 format).
    
    This function can be used in two ways:
    1. Pass date_obj (date) + time_obj (time) + optional local_tz
    2. Pass date_obj (datetime) + time_obj (timezone name as string)
    
    Args:
        date_obj: Python date object OR datetime object
        time_obj: Python time object OR timezone name string
        local_tz: Timezone object or string (if None, auto-detects system timezone)
    
    Returns:
        ISO format string in UTC timezone (RFC3339)
    """
    
    # Case 1: date_obj is a datetime, time_obj is a timezone name string
    # This is the to_utc_rfc3339 pattern from freebusy.py
    if isinstance(date_obj, datetime) and isinstance(time_obj, str):
        local_dt = date_obj
        tz_name = time_obj
        tz = ZoneInfo(tz_name)
        local = local_dt.replace(tzinfo=tz)
        utc = local.astimezone(timezone.utc)
        return utc.isoformat()
    
    # Case 2: traditional usage with separate date and time objects
    if isinstance(time_obj, timedelta):
        raise ValueError("Duration cannot be converted to ISO start time.")
    
    # Auto-detect timezone if not provided
    if local_tz is None:
        local_tz = get_local_timezone()
    
    # Handle timezone as string (convert to ZoneInfo)
    if isinstance(local_tz, str):
        local_tz = ZoneInfo(local_tz)
    
    # Combine date and time into naive datetime
    dt = datetime.combine(date_obj, time_obj)
    
    # Make timezone-aware using local timezone
    # Works with both ZoneInfo and datetime.timezone objects
    dt_local = dt.replace(tzinfo=local_tz)
    
    # Convert to UTC
    dt_utc = dt_local.astimezone(timezone.utc)
    
    return dt_utc.isoformat()


def get_current_datetime_context():
    """Get current date/time information for the agent."""
    now = datetime.now()
    return f"""
Current date and time: {now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%A, %B %d, %Y')})

When users say:
- "tomorrow" → use date: {(now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).strftime('%Y-%m-%d')}
- "today" → use date: {now.strftime('%Y-%m-%d')}
- "next week" → add 7 days from today
- "in 2 hours" → calculate from current time: {now.strftime('%H:%M')}
    """.strip()
