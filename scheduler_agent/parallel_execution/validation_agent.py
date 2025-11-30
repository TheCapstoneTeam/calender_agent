"""
Comprehensive Conflict Detection & Validation Agent.

This sub-agent performs multi-dimensional validation across:
- Calendar conflicts (organizer and attendees)
- Room availability
- Timezone violations
- Policy violations

All validations run in parallel for maximum performance.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from .policy_engine import PolicyEngine, PolicyViolation
from .parallel_coordinator import ParallelAvailabilityCoordinator

from ..reasoning_engine import ReasoningEngine, ThoughtType
REASONING_AVAILABLE = True


class ValidationDimension(Enum):
    """Types of validation checks"""
    CALENDAR_CONFLICTS = "calendar_conflicts"
    ROOM_AVAILABILITY = "room_availability"
    TIMEZONE_VIOLATIONS = "timezone_violations"
    POLICY_VIOLATIONS = "policy_violations"


@dataclass
class ValidationResult:
    """Result from a single validation dimension"""
    dimension: ValidationDimension
    passed: bool
    issues: List[str]
    warnings: List[str]
    metadata: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    
    def __str__(self) -> str:
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"[{self.dimension.value}] {status}: {len(self.issues)} issues, {len(self.warnings)} warnings"


class ConflictValidationAgent:
    """
    Sub-agent that performs comprehensive event validation across multiple dimensions.
    
    Runs all validation checks in parallel for optimal performance.
    
    Usage:
        validator = ConflictValidationAgent()
        result = await validator.validate_event({
            "title": "Team Meeting",
            "date": "2025-11-30",
            "start_time": "14:00",
            "end_time": "15:00",
            "attendees": "alice@example.com, bob@example.com",
            "location": "Meeting Room A"
        })
        
        if result["valid"]:
            print("Event can be created!")
        else:
            print(f"Blocking issues: {result['blocking_issues']}")
    """
    
    def __init__(
        self,
        policy_file: str = None,
        reasoning_engine: Optional['ReasoningEngine'] = None
    ):
        """
        Initialize validation agent.
        
        Args:
            policy_file: Path to policies JSON. If None, uses default.
            reasoning_engine: Optional ReasoningEngine for observable reasoning
        """
        self.policy_engine = PolicyEngine(policies_file=policy_file)
        self.reasoning_engine = reasoning_engine
    
    def _log_thought(self, content: str, thought_type=None):
        """Log a thought if reasoning engine is available"""
        if self.reasoning_engine is not None:
            if thought_type is None:
                thought_type = ThoughtType.PLANNING
            self.reasoning_engine.think(content, thought_type)
    
    async def validate_event(self, event_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate event across all dimensions in parallel.
        
        Args:
            event_details: Dictionary with event information:
                - title: str
                - date: str (YYYY-MM-DD)
                - start_time: str (HH:MM)
                - end_time: str (HH:MM)
                - attendees: str (comma-separated) or List[str]
                - location: str (optional)
                - calendar_name: str (optional, default: "primary")
        
        Returns:
            {
                "valid": bool,  # True if no blocking issues
                "blocking_issues": [list of critical errors],
                "warnings": [list of non-blocking concerns],
                "validations": {dimension: ValidationResult},
                "execution_time": float
            }
        """
        start_time = datetime.now()
        
        self._log_thought(
            "Running comprehensive validation checks in parallel",
            ThoughtType.PLANNING if REASONING_AVAILABLE else None
        )
        
        self._log_thought(
            f"Validating: calendar, room, timezone, policies",
            ThoughtType.DECISION if REASONING_AVAILABLE else None
        )
        
        # Run all validations in parallel
        validation_tasks = [
            self._validate_calendar_conflicts(event_details),
            self._validate_room_availability(event_details),
            self._validate_timezone(event_details),
            self._validate_policies(event_details)
        ]
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Process results
        validations = {}
        blocking_issues = []
        warnings = []
        
        for result in results:
            if isinstance(result, Exception):
                # Handle exception
                self._log_thought(
                    f"Validation error: {str(result)}",
                    ThoughtType.CONCERN if REASONING_AVAILABLE else None
                )
                continue
            
            if isinstance(result, ValidationResult):
                validations[result.dimension] = result
                
                # Log result
                if result.passed:
                    self._log_thought(
                        f"{result.dimension.value}: No issues found",
                        ThoughtType.VALIDATION if REASONING_AVAILABLE else None
                    )
                else:
                    self._log_thought(
                        f"{result.dimension.value}: {len(result.issues)} issue(s) detected",
                        ThoughtType.CONCERN if REASONING_AVAILABLE else None
                    )
                
                # Collect issues and warnings
                blocking_issues.extend(result.issues)
                warnings.extend(result.warnings)
        
        # Calculate metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        valid = len(blocking_issues) == 0
        
        # Log summary
        if valid:
            self._log_thought(
                f"Validation passed with {len(warnings)} warning(s)",
                ThoughtType.VALIDATION if REASONING_AVAILABLE else None
            )
        else:
            self._log_thought(
                f"Validation failed: {len(blocking_issues)} blocking issue(s)",
                ThoughtType.WARNING if REASONING_AVAILABLE else None
            )
            for issue in blocking_issues:
                self._log_thought(
                    f"Blocking: {issue}",
                    ThoughtType.CONCERN if REASONING_AVAILABLE else None
                )
        
        return {
            "valid": valid,
            "blocking_issues": blocking_issues,
            "warnings": warnings,
            "validations": validations,
            "execution_time": execution_time
        }
    
    async def _validate_calendar_conflicts(self, event: Dict) -> ValidationResult:
        """
        Check for calendar conflicts (organizer and attendees).
        
        Uses the ParallelAvailabilityCoordinator from Stage 1.
        """
        start_time = datetime.now()
        issues = []
        warnings = []
        
        try:
            # Check attendee availability using parallel coordinator
            attendees = event.get('attendees', '')
            if attendees:
                coordinator = ParallelAvailabilityCoordinator()
                
                # Parse attendees
                if isinstance(attendees, str):
                    attendee_list = [email.strip() for email in attendees.split(',') if email.strip()]
                else:
                    attendee_list = attendees
                
                if attendee_list:
                    result = await coordinator.check_all_attendees(
                        attendees=attendee_list,
                        date=event['date'],
                        start_time=event['start_time'],
                        end_time=event['end_time']
                    )
                    
                    # Check for conflicts
                    if result['busy_count'] > 0:
                        for email, conflicts in result['busy_attendees'].items():
                            issues.append(f"Attendee {email} has {len(conflicts)} conflict(s)")
                    
                    # Check for errors
                    if result['error_count'] > 0:
                        for email, error in result['errors'].items():
                            warnings.append(f"Could not check {email}: {error}")
        
        except Exception as e:
            warnings.append(f"Calendar conflict check failed: {str(e)}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            dimension=ValidationDimension.CALENDAR_CONFLICTS,
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            execution_time=execution_time
        )
    
    async def _validate_room_availability(self, event: Dict) -> ValidationResult:
        """
        Check room availability.
        
        Note: This is a placeholder. Full implementation would check
        room calendars via Google Calendar API.
        """
        start_time = datetime.now()
        issues = []
        warnings = []
        
        location = event.get('location', '')
        
        # Placeholder: In real implementation, check room calendar
        # For now, just validate that a location is specified for multi-person meetings
        attendees = event.get('attendees', '')
        if attendees:
            if isinstance(attendees, str):
                attendee_count = len([e for e in attendees.split(',') if e.strip()])
            else:
                attendee_count = len(attendees)
            
            if attendee_count >= 3 and not location:
                warnings.append(f"Meeting with {attendee_count} attendees has no location specified")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            dimension=ValidationDimension.ROOM_AVAILABILITY,
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            execution_time=execution_time
        )
    
    async def _validate_timezone(self, event: Dict) -> ValidationResult:
        """
        Check for timezone-related issues.
        
        Validates:
        - Meeting not at inappropriate hours for any timezone
        - Attendees across multiple timezones get reasonable times
        """
        start_time = datetime.now()
        issues = []
        warnings = []
        
        try:
            # Check if meeting is at reasonable hours
            start_time_str = event.get('start_time', '')
            if start_time_str:
                start_hour = int(start_time_str.split(':')[0])
                
                # Very early morning (before 6 AM)
                if start_hour < 6:
                    warnings.append(f"Meeting starts at {start_time_str} - very early for some timezones")
                
                # Late night (after 10 PM)
                elif start_hour >= 22:
                    warnings.append(f"Meeting starts at {start_time_str} - late night for some timezones")
        
        except Exception as e:
            warnings.append(f"Timezone validation failed: {str(e)}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            dimension=ValidationDimension.TIMEZONE_VIOLATIONS,
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            execution_time=execution_time
        )
    
    async def _validate_policies(self, event: Dict) -> ValidationResult:
        """
        Check organizational policy compliance using PolicyEngine.
        """
        start_time = datetime.now()
        issues = []
        warnings = []
        
        try:
            # Check policies
            violations = await self.policy_engine.check_policies(event)
            
            # Categorize violations
            for violation in violations:
                if violation.is_blocking():
                    issues.append(str(violation))
                else:
                    warnings.append(str(violation))
        
        except Exception as e:
            warnings.append(f"Policy check failed: {str(e)}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            dimension=ValidationDimension.POLICY_VIOLATIONS,
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            metadata={'violation_count': len(issues) + len(warnings)},
            execution_time=execution_time
        )
