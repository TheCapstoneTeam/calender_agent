import pytz
from datetime import datetime, timedelta, timezone
from .auth import get_calendar_service

# --------------------------
#  Timezone Helpers
# --------------------------

def get_local_timezone():
    """
    Auto-detect the system's local timezone.
    Returns a pytz timezone object.
    """
    # Get local timezone using datetime
    local_tz = datetime.now().astimezone().tzinfo
    # Convert to pytz timezone for consistency
    return local_tz


# --------------------------
#  Date & Time Helpers
# --------------------------

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


def to_iso(date_obj, time_obj, local_tz=None):
    """
    Convert date + time (or timedelta) into ISO string in UTC.
    
    Args:
        date_obj: Python date object
        time_obj: Python time object or timedelta
        local_tz: Timezone object (if None, auto-detects system timezone)
    
    Returns:
        ISO format string in UTC timezone
    """
    if isinstance(time_obj, timedelta):
        raise ValueError("Duration cannot be converted to ISO start time.")
    
    # Auto-detect timezone if not provided
    if local_tz is None:
        local_tz = get_local_timezone()
    
    # Combine date and time into naive datetime
    dt = datetime.combine(date_obj, time_obj)
    
    # Make timezone-aware using local timezone
    if hasattr(local_tz, 'localize'):
        # pytz timezone
        dt_local = local_tz.localize(dt)
    else:
        # datetime.timezone object
        dt_local = dt.replace(tzinfo=local_tz)
    
    # Convert to UTC
    dt_utc = dt_local.astimezone(timezone.utc)
    
    return dt_utc.isoformat()



# --------------------------
#  Event Tools
# --------------------------

def create_event(title: str, date: str, start_time: str, end_time: str, attendees: str = ""):
    """
    Creates event with timezone-aware times in UTC.

    Args:
        title: Event title
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "11:15"
        end_time: End time "13:15" OR duration like "2hr"
        attendees: Comma-separated email addresses (optional)
    
    Returns:
        Dictionary with event details including UTC timestamps
    """

    service = get_calendar_service()
    
    # Get local timezone for interpreting naive times
    local_tz = get_local_timezone()

    # Parse date
    date_obj = parse_date(date)

    # Parse start time (always absolute)
    start_t = parse_time(start_time)
    if isinstance(start_t, timedelta):
        raise ValueError("Start time cannot be a duration.")

    # Handle end time (duration OR absolute)
    end_t = parse_time(end_time)

    if isinstance(end_t, timedelta):
        # duration → convert into end clock time
        dt_start = datetime.combine(date_obj, start_t)
        dt_end = dt_start + end_t
        end_t = dt_end.time()

    # Convert to ISO in UTC
    start_iso = to_iso(date_obj, start_t, local_tz)
    end_iso = to_iso(date_obj, end_t, local_tz)

    # Validate that event is not in the past
    dt_start_local = datetime.combine(date_obj, start_t)
    if hasattr(local_tz, 'localize'):
        dt_start_aware = local_tz.localize(dt_start_local)
    else:
        dt_start_aware = dt_start_local.replace(tzinfo=local_tz)
    
    now = datetime.now(tz=local_tz)
    if dt_start_aware < now:
        raise ValueError(
            f"Cannot create events in the past. "
            f"Event start time {dt_start_aware.strftime('%Y-%m-%d %H:%M')} "
            f"is before current time {now.strftime('%Y-%m-%d %H:%M')}"
        )

    # Build event with UTC timezone
    event_body = {
        "summary": title,
        "start": {"dateTime": start_iso, "timeZone": "UTC"},
        "end": {"dateTime": end_iso, "timeZone": "UTC"}
    }
    
    # Add attendees if provided
    if attendees and attendees.strip():
        # Parse comma-separated email addresses
        attendee_list = [email.strip() for email in attendees.split(",") if email.strip()]
        event_body["attendees"] = [{"email": email} for email in attendee_list]

    event = service.events().insert(
        calendarId="primary", 
        body=event_body,
        sendUpdates="all"  # Send email notifications to all attendees
    ).execute()

    return {
        "status": "success",
        "event_id": event.get("id"),
        "start": start_iso,
        "end": end_iso,
        "attendees": attendees if attendees else "none"
    }




def check_conflict(date: str, start_time: str, end_time: str):
    """
    Checks overlapping events using UTC timezone.
    
    Args:
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "11:15"
        end_time: End time "13:15" OR duration "2hr"
    
    Returns:
        Dictionary with conflict status and event details
    """

    service = get_calendar_service()
    
    # Get local timezone for interpreting naive times
    local_tz = get_local_timezone()

    date_obj = parse_date(date)
    start_t = parse_time(start_time)
    end_t = parse_time(end_time)

    # Duration → convert to final time
    if isinstance(end_t, timedelta):
        dt_start = datetime.combine(date_obj, start_t)
        dt_end = dt_start + end_t
        end_t = dt_end.time()

    # Convert both to UTC RFC3339 timestamps
    start_iso = to_iso(date_obj, start_t, local_tz)
    end_iso = to_iso(date_obj, end_t, local_tz)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_iso,
        timeMax=end_iso,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    return {
        "conflict": len(events) > 0,
        "events": events,
        "start": start_iso,
        "end": end_iso
    }

