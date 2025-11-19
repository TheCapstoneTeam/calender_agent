# agent.py

from google.adk.agents import LlmAgent
from capstoneproject.calendar_tools import create_event
from capstoneproject.auth import get_api_key


# Ensure API key is loaded into the environment for ADK / genai libs to use
get_api_key()

# ADK requires a module-level variable named `root_agent` for the CLI to discover
root_agent = LlmAgent(
    name="calendar_agent",   # valid identifier: no hyphens
    model="gemini-2.5-flash",  # model specified as string
    tools=[create_event],
)
