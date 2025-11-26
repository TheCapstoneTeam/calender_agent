from google.adk.agents import LlmAgent
from .config import get_api_key, get_current_datetime_context
from .calendar_tools import create_event, check_conflict
from datetime import datetime

get_api_key()
get_current_datetime_context()


root_agent = LlmAgent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description="Schedules Google Calendar events after checking for conflicts to ensure attendees are free.",
    instruction=f"""
    {get_current_datetime_context()}

    When the user wants to schedule a meeting:
    1. Parse the natural language input to extract:
    - Date (convert relative dates like "tomorrow" to YYYY-MM-DD format)
    - Start time (HH:MM format)
    - End time (HH:MM format OR duration like "1hr", "2h", "30min")
    - Event title
    - Attendees (comma-separated email addresses, optional)
    2. Call `check_conflict` with the parsed date, start_time, and end_time
    3. If there is no conflict, call `create_event` with all parameters including attendees
    4. If there is a conflict, inform the user about the conflicting events

    Date formats accepted: YYYY-MM-DD or DD-MM-YYYY
    Time formats: "HH:MM" (e.g., "14:30") or duration (e.g., "1hr", "2h", "30min")
    Attendees format: comma-separated emails (e.g., "user1@gmail.com, user2@gmail.com")
    """.strip(),
    tools=[create_event, check_conflict],
)
