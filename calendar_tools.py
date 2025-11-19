# calendar_tools.py

def create_event(title: str, date: str, time: str | None = None, description: str | None = None) -> dict:
    """
    Create a calendar event (mock).
    Args:
      title: event title
      date: date string 'YYYY-MM-DD' (or natural-language if you parse it elsewhere)
      time: 'HH:MM' optional
      description: optional text
    Returns:
      dict with status and summary (agent will show this to user)
    """
    # In the real implementation replace this block with Google Calendar API calls
    start = f"{date}T{time}:00" if time else f"{date}"
    event = {
        "status": "ok",
        "message": f"Mock event created: {title} at {start}",
        "title": title,
        "start": start,
        "description": description or ""
    }
    return event
