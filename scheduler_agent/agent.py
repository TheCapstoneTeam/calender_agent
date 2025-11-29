from google.adk.tools.google_search_tool import GoogleSearchTool

from google.adk.agents import LlmAgent
from .auth import get_api_key
from .datetime_utils import get_current_datetime_context
from .calendar_tools import (
    create_event, check_conflict, validate_emails, 
    get_team_members, find_facility, get_facility_info
)
from datetime import datetime
import os

get_api_key()

search_tool_instance = GoogleSearchTool(bypass_multi_tools_limit=True)

root_agent = LlmAgent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description="Schedules Google Calendar events with mandatory location collection, smart holiday checks, and conflict resolution.",
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
    - Team Name (e.g., "TeamElla", "TeamWonders")
    - Facility Requirements (e.g., "room for 5", "projector")
    
    2. **Resolve Attendees**:
       - If a Team Name is mentioned, call `get_team_members` to get the list of emails.
       - Combine these with any explicitly mentioned attendees.
    
    3. **Resolve Facility/Location**:
       - If a specific room is requested, use it as the location.
       - If requirements are given (capacity, amenities) but no room is named, call `find_facility` to find suitable options.
       - Ask the user to confirm the room if multiple options are found or if the choice is ambiguous.

    4. **CRITICAL STEP**: If attendees are provided (from team lookup or direct input), you MUST first call `validate_emails` with the list of email addresses.
       - If `validate_emails` returns invalid emails or typos:
         - Inform the user about the invalid emails and the reason.
         - If there are typo suggestions, ask the user if they meant the suggested known email domains.
         - **DO NOT** proceed to create the event until the user confirms or corrects the emails.
       - If all emails are valid (or after user correction), proceed to the next step.

    5. Call `check_conflict` with the parsed date, start_time, end_time, and validated emails
    6. If there is no conflict, call `create_event` with all parameters including valid attendees and the target calendar name (if specified)
    7. If there is a conflict, inform the user about the conflicting events
    ===============================
    🔵 MANDATORY LOCATION COLLECTION
    ===============================

    Before performing ANY action — including holiday checking, conflict checking, or scheduling —
    you MUST confirm the **location (country)** of the meeting attendees.

    Workflow:
    - Extract the attendees (emails or names).
    - Check if their country is known (from user input, email domain, or context).
    - If NOT known:
         ➤ STOP immediately.
         ➤ Ask the user: 
           "Before I proceed, what is the location (country) of the attendees?"
         ➤ WAIT for the user response.
    - Only after the location is confirmed → continue the scheduling workflow.


    ===============================
    🔵 HOLIDAY CHECKING (SEARCH-BASED, LOCATION-SPECIFIC)
    ===============================

    After location is known:

    You MUST use `google_search` to check holidays relevant to that exact country.

    Example queries:
    - "Is <YYYY-MM-DD> a holiday in <country>?"
    - "<country> public holiday <YYYY-MM-DD>"

    ✔ If any relevant holiday is detected:
       - Do NOT schedule.
       - Tell the user: 
         "This date may be a holiday in <country>: <summary>. Do you still want me to schedule it?"
       - WAIT for confirmation.

    ✔ If no holiday found → continue normally.


    ===============================
    🔵 MEETING SCHEDULING WORKFLOW
    ===============================

    1. Parse from user:
       - Date (convert “tomorrow”, “next Monday”, etc. → YYYY-MM-DD)
       - Start time
       - End time or duration
       - Event title
       - Attendees (optional, comma-separated emails)
       - Calendar name (default: primary)

    2. Validate attendees:
       - Call `validate_emails`
       - If invalid → inform user → WAIT.

    3. Confirm attendee location (MANDATORY):
       - Ask user if not known.

    4. Holiday check (location-specific):
       - As described above.

    5. Check conflicts:
       - Call `check_conflict`.

    6. If no conflict & no holiday block:
       - Call `create_event`.

    ===============================
    Acceptable Formats
    ===============================
    Date: YYYY-MM-DD or DD-MM-YYYY  
    Time: "HH:MM" or duration ("1hr", "30 min")  
    Calendar: "on TeamElla calendar"
    """.strip(),

    tools=[
        validate_emails,
        check_conflict,
        create_event,
        search_tool_instance,
        get_team_members, 
        find_facility, 
        get_facility_info
    ],
)

