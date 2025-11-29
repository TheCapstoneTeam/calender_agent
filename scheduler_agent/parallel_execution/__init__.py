"""
Sub-agents package for the calendar scheduler.

This package contains specialized sub-agents that can run in parallel
to improve performance and capabilities.
"""

from .availability_checker import AvailabilityCheckerAgent
from .parallel_coordinator import ParallelAvailabilityCoordinator
from .policy_engine import PolicyEngine, PolicyViolation, PolicySeverity
from .validation_agent import ConflictValidationAgent, ValidationDimension, ValidationResult

__all__ = [
    # Stage 1: Parallel Availability Checking
    'AvailabilityCheckerAgent',
    'ParallelAvailabilityCoordinator',
    # Stage 2: Conflict Detection & Validation
    'PolicyEngine',
    'PolicyViolation',
    'PolicySeverity',
    'ConflictValidationAgent',
    'ValidationDimension',
    'ValidationResult',
]
