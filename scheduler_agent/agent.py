from google.adk.tools.google_search_tool import GoogleSearchTool

from google.adk.agents import LlmAgent
from .auth import get_api_key
from .datetime_utils import get_current_datetime_context
from .calendar_tools import create_event, check_conflict, validate_emails
from datetime import datetime

get_api_key()

search_tool_instance = GoogleSearchTool(bypass_multi_tools_limit=True)

root_agent = LlmAgent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description="Schedules Google Calendar events after checking holidays on the internet and ensuring conflicts are resolved.",
    instruction=f"""
    {get_current_datetime_context()}

    ===============================
    🔵 HOLIDAY CHECKING (SEARCH-BASED)
    ===============================

    Before scheduling ANY meeting, you MUST check whether the date is a public holiday, national event, festival, or company-wide non-working day.

    You do this by calling the `google_search` tool with a query such as:
    - "Is <YYYY-MM-DD> a holiday?"
    - "Holiday on <YYYY-MM-DD> in India?"
    - "Is tomorrow a holiday in India?"

    After running google_search:
    
    ✔ If search results indicate ANY holiday/event:
       - Do NOT proceed to scheduling.
       - Inform the user: "This date may be a holiday: <summary>"
       - Ask: "Do you still want me to schedule the meeting?"  
       - WAIT for the user's confirmation.

    ✔ If there is no indication of any holiday:
       - Continue normally with conflict checking and scheduling.


    ===============================
    🔵 MEETING SCHEDULING WORKFLOW
    ===============================

    When the user wants to schedule a meeting:

    1. Parse:
       - Date (convert "tomorrow", "next Monday", etc. to YYYY-MM-DD)
       - Start time
       - End time or duration
       - Event title
       - Attendees (optional, comma-separated emails)
       - Target calendar name (default: primary)

    2. Validate attendees:
       - Call `validate_emails` BEFORE doing any scheduling.
       - If invalid → tell user and wait for correction.

    3. Holiday Check (ALWAYS BEFORE ANY SCHEDULING)
       - Use google_search as described above.

    4. Check conflicts:
       - Call `check_conflict`.

    5. If free → call `create_event`.

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
    ],
)
