from datetime import datetime, timedelta
from capstoneproject.auth import get_calendar_service

def parse_date(date_str):
    # Convert DD-MM-YYYY → YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except:
        return date_str  # Maybe user already used YYYY-MM-DD

def create_event(title: str, date: str, start_time: str, end_time: str):
    """
    date: can be DD-MM-YYYY or YYYY-MM-DD
    time: HH:MM (24h)
    """
    service = get_calendar_service()

    # Convert the date
    iso_date = parse_date(date)

    # Build start & end datetime strings
    start_iso = f"{iso_date}T{start_time}:00+05:30"
    end_iso = f"{iso_date}T{end_time}:00+05:30"

    event = {
        "summary": title,
        "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"}
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    return {"status": "success", "event_id": event.get("id")}

def check_conflict(start: str, end: str) -> dict:
    """
    Checks for overlapping events within the given time range.
    Returns all conflicting events.
    """
    service = get_calendar_service()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    return {
        "conflict": len(events) > 0,
        "events": events
    }

