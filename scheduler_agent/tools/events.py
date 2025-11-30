from datetime import datetime, timedelta
from ..auth import get_calendar_service
from ..datetime_utils import get_local_timezone, parse_date, parse_time, to_iso
from .validation import check_conflict
from .availability import check_attendees_availability

def get_calendar_id(service, calendar_name: str) -> str:
    """
    Resolves a calendar name to its ID.
    Returns 'primary' if name is empty or not found.
    """
    if not calendar_name or calendar_name.lower() == 'primary':
        return 'primary'

    # List all calendars
    calendar_list = service.calendarList().list(minAccessRole='writer').execute()
    items = calendar_list.get('items', [])

    for cal in items:
        if cal.get('summary', '').lower() == calendar_name.lower():
            return cal.get('id')
    
    # Fallback to primary if not found (or maybe raise error? For now fallback is safer)
    print(f"Warning: Calendar '{calendar_name}' not found. Using 'primary'.")
    return 'primary'


def create_event(title: str, date: str, start_time: str, end_time: str, attendees: str = "", calendar_name: str = "primary"):
    """
    Creates event with timezone-aware times in UTC.

    Args:
        title: Event title
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "11:15"
        end_time: End time "13:15" OR duration like "2hr"
        attendees: Comma-separated email addresses (optional)
        calendar_name: Name of the calendar to create event on (default: "primary")
    
    Returns:
        Dictionary with event details including UTC timestamps
    """

    service = get_calendar_service()
    target_calendar_id = get_calendar_id(service, calendar_name)
    
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
        calendarId=target_calendar_id, 
        body=event_body,
        sendUpdates="all"  # Send email notifications to all attendees
    ).execute()

    return {
        "status": "success",
        "event_id": event.get("id"),
        "calendar_id": target_calendar_id,
        "start": start_iso,
        "end": end_iso,
        "attendees": attendees if attendees else "none"
    }


def create_event_with_attendees(title: str, date: str, start_time: str, end_time: str, attendees: str, organizer_tz: str = None, check_availability: bool = True, calendar_name: str = "primary"):
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
        calendar_name: Name of the calendar to create event on (default: "primary")
    
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
    event_result = create_event(title, date, start_time, end_time, attendees, calendar_name=calendar_name)
    
    # Get event link from the API
    service = get_calendar_service()
    event_id = event_result["event_id"]
    target_cal_id = event_result.get("calendar_id", "primary")
    event = service.events().get(calendarId=target_cal_id, eventId=event_id).execute()
    
    return {
        "status": "success",
        "message": f"Event '{title}' created successfully with {len(attendees.split(',')) if attendees else 0} attendee(s).",
        "event_id": event_id,
        "event_link": event.get("htmlLink"),
        "start": event_result["start"],
        "end": event_result["end"],
        "attendees": attendees
    }
