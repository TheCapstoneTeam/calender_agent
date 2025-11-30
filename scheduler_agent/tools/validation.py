from datetime import datetime, timedelta
from ..auth import get_calendar_service
from ..datetime_utils import get_local_timezone, parse_date, parse_time, to_iso
from ..parallel_execution import ConflictValidationAgent

def check_conflict(date: str, start_time: str, end_time: str, timezone: str = None):
    """
    Checks overlapping events across ALL user calendars using UTC timezone.
    
    Args:
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "11:15"
        end_time: End time "13:15" OR duration "2hr"
        timezone: Timezone name (e.g., 'Asia/Singapore'). If None, uses system timezone.
    
    Returns:
        Dictionary with conflict status and event details
    """

    service = get_calendar_service()
    
    # Get local timezone for interpreting naive times
    # If timezone is provided, use it. Otherwise default to system local.
    if timezone:
        local_tz = timezone
    else:
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
    # to_iso handles both string timezones and timezone objects
    start_iso = to_iso(date_obj, start_t, local_tz)
    end_iso = to_iso(date_obj, end_t, local_tz)

    # 1. Get all calendars
    calendar_list_result = service.calendarList().list(minAccessRole='reader').execute()
    calendars = calendar_list_result.get('items', [])

    all_conflicts = []

    # 2. Check each calendar
    for cal in calendars:
        cal_id = cal.get('id')
        # Skip if selected is False (hidden calendars)
        if not cal.get('selected', True):
            continue

        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if events:
            # Add calendar name to event details for clarity
            for event in events:
                event['calendarSummary'] = cal.get('summary', 'Unknown Calendar')
            all_conflicts.extend(events)

    return {
        "conflict": len(all_conflicts) > 0,
        "events": all_conflicts,
        "start": start_iso,
        "end": end_iso
    }


def check_policies(
    duration_hours: float,
    attendee_count: int,
    start_hour: int,
    day_of_week: str
) -> dict:
    """
    Check event against organizational policies.
    
    Args:
        duration_hours: Meeting duration in hours
        attendee_count: Number of attendees
        start_hour: Start hour (0-23)
        day_of_week: Day name (e.g., "Monday", "Saturday")
    
    Returns:
        {
            "allowed": bool,
            "violations": [...],
            "warnings": [...]
        }
    """
    violations = []
    warnings = []
    
    # Check duration
    if duration_hours > 4:
        warnings.append(f"Meeting duration ({duration_hours}hrs) exceeds 4 hour recommendation. Consider splitting into multiple sessions.")
    
    # Check attendee count - BLOCKING
    if attendee_count >= 20:
        violations.append(f"Large meetings ({attendee_count} attendees) with 20+ people require executive approval before scheduling.")
    
    # Check business hours
    if start_hour < 9 or start_hour >= 17:
        warnings.append(f"Meeting starts at {start_hour}:00, outside typical business hours (9 AM - 5 PM). Consider attendee timezones.")
    
    # Check weekend
    if day_of_week in ["Saturday", "Sunday"]:
        warnings.append(f"Meeting scheduled on {day_of_week}. Ensure all attendees are aware and willing to attend weekend meetings.")
    
    # Very early or very late
    if start_hour < 7:
        warnings.append(f"Meeting starts at {start_hour}:00 - very early morning. Consider timezones.")
    elif start_hour >= 20:
        warnings.append(f"Meeting starts at {start_hour}:00 - late evening. Consider timezones.")
    
    return {
        "allowed": len(violations) == 0,
        "violations": violations,
        "warnings": warnings
    }


async def validate_event_comprehensive(
    title: str,
    date: str,
    start_time: str,
    end_time: str,
    attendees: str = "",
    location: str = "",
    calendar_name: str = "primary",
    reasoning_engine = None
) -> dict:
    """
    Perform comprehensive validation across multiple dimensions:
    - Calendar conflicts (organizer and attendees)
    - Room availability
    - Timezone violations
    - Policy compliance
    
    All validations run in parallel for optimal performance.
    
    Args:
        title: Event title
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "HH:MM"
        end_time: End time "HH:MM" OR duration like "2hr"
        attendees: Comma-separated email addresses (optional)
        location: Event location/room (optional)
        calendar_name: Calendar to create event on (default: "primary")
        reasoning_engine: Optional ReasoningEngine for observable reasoning
    
    Returns:
        {
            "valid": bool,  # True if no blocking issues
            "blocking_issues": [list of critical errors that prevent creation],
            "warnings": [list of non-blocking concerns],
            "validations": {dimension: ValidationResult},
            "execution_time": float
        }
    """
    
    # Create validation agent
    validator = ConflictValidationAgent(reasoning_engine=reasoning_engine)
    
    # Prepare event details
    event_details = {
        "title": title,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "location": location,
        "calendar_name": calendar_name
    }
    
    # Run comprehensive validation
    result = await validator.validate_event(event_details)
    
    return result
