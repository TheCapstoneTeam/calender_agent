from datetime import datetime, timedelta
from ..auth import get_calendar_service
from ..datetime_utils import get_local_timezone, parse_date, parse_time, to_iso
from ..parallel_execution import ParallelAvailabilityCoordinator

from .holidays import is_working_time

def check_attendees_availability(attendees: str, date: str, start_time: str, end_time: str, organizer_tz: str = None):
    """
    Check if attendees are available during the specified time slot using Google Calendar FreeBusy API.
    Also checks working hours and holidays preferences.
    
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
        # 1. Check Calendar Busy/Free
        calendar_info = freebusy_result.get('calendars', {}).get(email, {})
        busy_times = calendar_info.get('busy', [])
        
        is_busy = False
        if busy_times:
            busy_attendees[email] = busy_times
            is_busy = True
            
        # 2. Check Working Hours / Holidays (Logic Check)
        # Only check if not already busy from calendar
        if not is_busy:
            # Format date and times for is_working_time check
            date_str = date_obj.strftime("%Y-%m-%d")
            start_time_str = start_t.strftime("%H:%M")
            end_time_str = end_t.strftime("%H:%M")
            
            working_status = is_working_time(date_str, start_time_str, end_time_str, email)
            if not working_status["is_working"]:
                is_busy = True
                if email not in busy_attendees:
                    busy_attendees[email] = []
                
                # Add a synthetic busy block
                busy_attendees[email].append({
                    "start": start_iso,
                    "end": end_iso,
                    "details": working_status["reason"]
                })
        
        if not is_busy:
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


async def check_attendees_availability_parallel(
    attendees: str,
    date: str,
    start_time: str,
    end_time: str,
    timezone: str = None,
    reasoning_engine = None
) -> dict:
    """
    Check attendee availability using parallel sub-agents for improved performance.
    
    This is the async version that spawns multiple AvailabilityChecker sub-agents
    to check attendees in parallel, achieving 5-10x speedup for large meetings.
    
    Args:
        attendees: Comma-separated email addresses
        date: Date string (DD-MM-YYYY or YYYY-MM-DD)
        start_time: Start time "HH:MM"
        end_time: End time "HH:MM" OR duration like "2hr"
        timezone: Timezone name (e.g., 'Asia/Singapore'). If None, uses system timezone
        reasoning_engine: Optional ReasoningEngine for observable reasoning
    
    Returns:
        Dictionary with availability information:
        {
            "all_available": bool,
            "available_count": int,
            "busy_count": int,
            "error_count": int,
            "available_attendees": [emails],
            "busy_attendees": {email: [conflicts]},
            "errors": {email: error_msg},
            "execution_time": float,
            "parallelization_factor": float
        }
    """
    
    # Parse attendees
    attendee_list = [email.strip() for email in attendees.split(",") if email.strip()]
    
    if not attendee_list:
        return {
            "all_available": True,
            "available_count": 0,
            "busy_count": 0,
            "error_count": 0,
            "available_attendees": [],
            "busy_attendees": {},
            "errors": {},
            "execution_time": 0.0,
            "parallelization_factor": 1.0
        }
    
    # Create coordinator and run parallel checks
    coordinator = ParallelAvailabilityCoordinator(
        timeout_seconds=3,
        max_parallel=50,
        reasoning_engine=reasoning_engine
    )
    
    result = await coordinator.check_all_attendees(
        attendees=attendee_list,
        date=date,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone
    )
    
    return result
