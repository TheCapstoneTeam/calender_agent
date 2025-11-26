from google.adk.agents import LlmAgent
from .auth import get_api_key
from .calendar_tools import create_event, check_conflict
from datetime import datetime

get_api_key()

def get_current_datetime_context():
    """Get current date/time information for the agent."""
    now = datetime.now()
    return f"""
Current date and time: {now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%A, %B %d, %Y')})

When users say:
- "tomorrow" → use date: {(now.replace(hour=0, minute=0, second=0, microsecond=0) + __import__('datetime').timedelta(days=1)).strftime('%Y-%m-%d')}
- "today" → use date: {now.strftime('%Y-%m-%d')}
- "next week" → add 7 days from today
- "in 2 hours" → calculate from current time: {now.strftime('%H:%M')}
    """.strip()

root_agent = LlmAgent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description="Schedules Google Calendar events and checks conflicts.",
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
