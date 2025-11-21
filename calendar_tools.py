import pytz
from datetime import datetime, timedelta
from .auth import get_calendar_service

IST = pytz.timezone("Asia/Kolkata")
now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

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


def to_iso(date_obj, time_obj):
    """
    Convert date + time (or timedelta) into ISO string
    """
    if isinstance(time_obj, timedelta):
        raise ValueError("Duration cannot be converted to ISO start time.")

    dt = datetime.combine(date_obj, time_obj)
    dt = IST.localize(dt)
    return dt.isoformat()


# --------------------------
#  Event Tools
# --------------------------

def create_event(title: str, date: str, start_time: str, end_time: str):
    """
    Creates event.

    start_time: "11:15"
    end_time: "13:15" OR duration like "2hr"
    """

    service = get_calendar_service()

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

    # Convert to ISO
    start_iso = to_iso(date_obj, start_t)
    end_iso = to_iso(date_obj, end_t)

    # Build event
    event_body = {
        "summary": title,
        "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"}
    }

    event = service.events().insert(
        calendarId="primary", body=event_body
    ).execute()

    return {
        "status": "success",
        "event_id": event.get("id"),
        "start": start_iso,
        "end": end_iso
    }


def check_conflict(date: str, start_time: str, end_time: str):
    """
    Checks overlapping events.
    start_time = "11:15"
    end_time = "13:15" OR duration "2hr"
    """

    service = get_calendar_service()

    date_obj = parse_date(date)
    start_t = parse_time(start_time)
    end_t = parse_time(end_time)

    # Duration → convert to final time
    if isinstance(end_t, timedelta):
        dt_start = datetime.combine(date_obj, start_t)
        dt_end = dt_start + end_t
        end_t = dt_end.time()

    # Convert both to *full RFC3339* timestamps
    start_iso = to_iso(date_obj, start_t)  # like 2025-11-21T11:15:00+05:30
    end_iso = to_iso(date_obj, end_t)      # like 2025-11-21T13:15:00+05:30

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
