from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .config import get_calendar_service

# --------------------------
#  Timezone Helpers
# --------------------------

def get_local_timezone():
    """
    Auto-detect the system's local timezone.
    Returns a timezone object (ZoneInfo or datetime.timezone).
    """
    # Get local timezone using datetime
    local_tz = datetime.now().astimezone().tzinfo
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
    
    Examples:
        >>> to_iso(date(2025, 11, 23), time(11, 0), 'Asia/Singapore')
        '2025-11-23T03:00:00+00:00'
        
        >>> to_iso(datetime(2025, 11, 23, 11, 0), 'Asia/Singapore')
        '2025-11-23T03:00:00+00:00'
    """
    from zoneinfo import ZoneInfo
    
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
        # Get organizer's email to prevent duplicates
        primary_cal = service.calendars().get(calendarId='primary').execute()
        organizer_email = primary_cal.get('id', '')
        
        # Parse comma-separated email addresses and filter out organizer
        attendee_list = [
            email.strip() for email in attendees.split(",") 
            if email.strip() and email.strip().lower() != organizer_email.lower()
        ]
        
        if attendee_list:
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


def check_attendees_availability(attendees: str, date: str, start_time: str, end_time: str, organizer_tz: str = None):
    """
    Check if attendees are available during the specified time slot using Google Calendar FreeBusy API.
    
    Args:
        attendees: Comma-separated email addresses
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "11:15"
        end_time: End time "13:15" OR duration like "2hr"
        organizer_tz: Timezone name (e.g., 'Asia/Singapore'). If None, uses system timezone
    
    Returns:
        Dictionary with availability information:
        {
            "all_free": bool,
            "busy_attendees": {"email@example.com": [{"start": "...", "end": "..."}], ...},
            "free_attendees": ["email@example.com", ...],
            "start": iso_string,
            "end": iso_string
        }
    """
    service = get_calendar_service()
    
    # Get timezone
    if organizer_tz is None:
        organizer_tz = get_local_timezone()
        # Convert to string if it's a timezone object
        if hasattr(organizer_tz, 'zone'):
            organizer_tz = organizer_tz.zone
        else:
            organizer_tz = 'UTC'
    
    # Parse inputs
    date_obj = parse_date(date)
    start_t = parse_time(start_time)
    end_t = parse_time(end_time)
    
    if isinstance(start_t, timedelta):
        raise ValueError("Start time cannot be a duration.")
    
    # Convert duration to end time if needed
    if isinstance(end_t, timedelta):
        dt_start = datetime.combine(date_obj, start_t)
        dt_end = dt_start + end_t
        end_t = dt_end.time()
        date_obj_end = dt_end.date()
    else:
        date_obj_end = date_obj
    
    # Convert to UTC ISO format for API
    start_iso = to_iso(date_obj, start_t, organizer_tz)
    end_iso = to_iso(date_obj_end, end_t, organizer_tz)
    
    # Parse attendees
    attendee_emails = [email.strip() for email in attendees.split(",") if email.strip()]
    
    if not attendee_emails:
        return {
            "all_free": True,
            "busy_attendees": {},
            "free_attendees": [],
            "start": start_iso,
            "end": end_iso
        }
    
    # Query FreeBusy API
    body = {
        "timeMin": start_iso,
        "timeMax": end_iso,
        "timeZone": "UTC",
        "items": [{"id": email} for email in attendee_emails]
    }
    
    freebusy_result = service.freebusy().query(body=body).execute()
    
    # Parse results
    busy_attendees = {}
    free_attendees = []
    
    for email in attendee_emails:
        calendar_info = freebusy_result.get('calendars', {}).get(email, {})
        busy_times = calendar_info.get('busy', [])
        
        if busy_times:
            busy_attendees[email] = busy_times
        else:
            free_attendees.append(email)
    
    return {
        "all_free": len(busy_attendees) == 0,
        "busy_attendees": busy_attendees,
        "free_attendees": free_attendees,
        "start": start_iso,
        "end": end_iso
    }


def all_attendees_free(availability_result: dict) -> bool:
    """
    Helper function to check if all attendees are free.
    
    Args:
        availability_result: Result from check_attendees_availability()
    
    Returns:
        True if all attendees are free, False otherwise
    """
    return availability_result.get("all_free", False)


def create_event_with_attendees(title: str, date: str, start_time: str, end_time: str, attendees: str, organizer_tz: str = None, check_availability: bool = True):
    """
    Create an event with attendees, optionally checking availability first.
    
    This function orchestrates the full event creation flow:
    1. Check organizer's calendar for conflicts
    2. Check attendees' availability (if check_availability=True)
    3. Create event if all are free
    
    Args:
        title: Event title
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "11:15"
        end_time: End time "13:15" OR duration like "2hr"
        attendees: Comma-separated email addresses
        organizer_tz: Timezone name (e.g., 'Asia/Singapore'). If None, uses system timezone
        check_availability: If True, checks attendee availability before creating event
    
    Returns:
        Dictionary with creation status:
        {
            "status": "success" | "organizer_conflict" | "attendees_busy",
            "message": "...",
            "organizer_conflicts": [...],  # if organizer has conflicts
            "busy_attendees": {...},  # if attendees are busy
            "event_id": "...",  # if created successfully
            "event_link": "..."  # if created successfully
        }
    """
    # Step 1: Check organizer's calendar
    organizer_conflict = check_conflict(date, start_time, end_time)
    
    if organizer_conflict["conflict"]:
        return {
            "status": "organizer_conflict",
            "message": f"You have {len(organizer_conflict['events'])} conflicting event(s) during this time slot.",
            "organizer_conflicts": organizer_conflict["events"],
            "start": organizer_conflict["start"],
            "end": organizer_conflict["end"]
        }
    
    # Step 2: Check attendees availability (if requested)
    if check_availability and attendees and attendees.strip():
        availability = check_attendees_availability(attendees, date, start_time, end_time, organizer_tz)
        
        if not availability["all_free"]:
            busy_details = []
            for email, busy_times in availability["busy_attendees"].items():
                busy_details.append(f"{email}: {len(busy_times)} busy slot(s)")
            
            return {
                "status": "attendees_busy",
                "message": f"Some attendees are busy: {', '.join(busy_details)}",
                "busy_attendees": availability["busy_attendees"],
                "free_attendees": availability["free_attendees"],
                "start": availability["start"],
                "end": availability["end"]
            }
    
    # Step 3: All clear - create the event
    event_result = create_event(title, date, start_time, end_time, attendees)
    
    # Get event link from the API
    service = get_calendar_service()
    event_id = event_result["event_id"]
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    
    return {
        "status": "success",
        "message": f"Event '{title}' created successfully with {len(attendees.split(',')) if attendees else 0} attendee(s).",
        "event_id": event_id,
        "event_link": event.get("htmlLink"),
        "start": event_result["start"],
        "end": event_result["end"],
        "attendees": attendees
    }

