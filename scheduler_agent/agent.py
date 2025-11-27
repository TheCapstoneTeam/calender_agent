from google.adk.agents import LlmAgent
from .auth import get_api_key
from .datetime_utils import get_current_datetime_context
from .calendar_tools import create_event, check_conflict, validate_emails
from datetime import datetime

get_api_key()

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
    - Target Calendar (e.g., "TeamElla", default to "primary" if not specified)
    
    2. **CRITICAL STEP**: If attendees are provided, you MUST first call `validate_emails` with the list of email addresses.
       - If `validate_emails` returns invalid emails or typos:
         - Inform the user about the invalid emails and the reason.
         - If there are typo suggestions, ask the user if they meant the suggested known email domains.
         - **DO NOT** proceed to create the event until the user confirms or corrects the emails.
       - If all emails are valid (or after user correction), proceed to the next step.

    3. Call `check_conflict` with the parsed date, start_time, end_time, and validated emails
    4. If there is no conflict, call `create_event` with all parameters including valid attendees and the target calendar name (if specified)
    5. If there is a conflict, inform the user about the conflicting events

    Date formats accepted: YYYY-MM-DD or DD-MM-YYYY
    Time formats: "HH:MM" (e.g., "14:30") or duration (e.g., "1hr", "2h", "30min")
    Attendees format: comma-separated emails (e.g., "user1@gmail.com, user2@gmail.com")
    Calendar format: "on [Calendar Name] calendar" (e.g., "on TeamElla calendar")
    """.strip(),
    tools=[create_event, check_conflict, validate_emails],
)
