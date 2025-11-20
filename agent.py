# agent.py

from google.adk.agents import LlmAgent
from capstoneproject.auth import get_api_key
from capstoneproject.calendar_tools import create_event, check_conflict
# Load API key so ADK can use Gemini
get_api_key()

# Root agent required by ADK
root_agent = LlmAgent(
    name="calendar_agent",
    model="gemini-2.5-flash",   # your LLM
    description="An agent that can schedule Google Calendar events using OAuth.",
    instruction=(
        "When the user asks to schedule or create an event, "
        "use the create_event tool with correct parameters."
    ),
    tools=[create_event,check_conflict],  # <-- This is your TOOL for Calendar
)
