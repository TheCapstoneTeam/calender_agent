"""
ADK Sub-Agents for Calendar Scheduler

This package contains proper Google ADK Agent instances that use the
sub_agents parameter for hierarchical multi-agent architecture.

Sub-Agents:
- availability_checker: Checks attendee availability
- event_validator: Validates events against policies
- facility_manager: Manages meeting room booking
- event_creator: Creates calendar events

Note: For advanced parallel execution implementation, see ../parallel_execution/
"""

from .availability_agent import availability_checker_agent
from .validator_agent import event_validator_agent
from .facility_agent import facility_manager_agent
from .creator_agent import event_creator_agent

__all__ = [
    'availability_checker_agent',
    'event_validator_agent',
    'facility_manager_agent',
    'event_creator_agent',
]
