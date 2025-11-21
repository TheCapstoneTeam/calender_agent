from google.adk.agents import LlmAgent
from calendar_agent.auth import get_api_key
from calendar_agent.calendar_tools import create_event, check_conflict

get_api_key()

root_agent = LlmAgent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description="Schedules Google Calendar events and checks conflicts.",
    instruction=(
        "When the user wants to schedule a meeting, first call "
        "`check_conflict` with date, start_time, end_time. "
        "If there is no conflict, call `create_event`."
    ),
    tools=[create_event, check_conflict],
)
