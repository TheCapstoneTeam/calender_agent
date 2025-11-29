"""
Policy Engine for organizational rule checking.

Loads and enforces configurable policies for meeting scheduling,
including duration limits, attendee counts, business hours, etc.
"""

import json
from pathlib import Path
from datetime import datetime, time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PolicySeverity(Enum):
    """Severity levels for policy violations"""
    INFO = "info"           # Informational, doesn't block
    WARNING = "warning"     # Recommends change, doesn't block
    ERROR = "error"         # Blocks event creation


@dataclass
class PolicyViolation:
    """Represents a single policy violation"""
    policy_id: str
    policy_name: str
    severity: PolicySeverity
    message: str
    metadata: Optional[Dict[str, Any]] = None
    
    def is_blocking(self) -> bool:
        """Check if this violation blocks event creation"""
        return self.severity == PolicySeverity.ERROR
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        severity_emoji = {
            PolicySeverity.INFO: "ℹ️",
            PolicySeverity.WARNING: "⚠️",
            PolicySeverity.ERROR: "❌"
        }
        emoji = severity_emoji.get(self.severity, "")
        return f"{emoji} [{self.severity.value.upper()}] {self.policy_name}: {self.message}"


class PolicyEngine:
    """
    Manages and checks organizational policies for event scheduling.
    
    Policies are loaded from a JSON file and can be enabled/disabled.
    Each policy has a severity level (info/warning/error).
    
    Usage:
        engine = PolicyEngine()
        violations = await engine.check_policies({
            "date": "2025-11-30",
            "start_time": "14:00",
            "end_time": "18:30",
            "attendees": ["alice@example.com", "bob@example.com", ...]
        })
        
        if any(v.is_blocking() for v in violations):
            print("Cannot create event - policy violations!")
    """
    
    def __init__(self, policies_file: str = None):
        """
        Initialize policy engine.
        
        Args:
            policies_file: Path to policies JSON file. If None, uses default location.
        """
        if policies_file is None:
            # Default to data/policies.json relative to project root
            project_root = Path(__file__).parent.parent.parent
            policies_file = project_root / "data" / "policies.json"
        
        self.policies_file = Path(policies_file)
        self.policies = self._load_policies()
    
    def _load_policies(self) -> List[Dict[str, Any]]:
        """Load policies from JSON file"""
        if not self.policies_file.exists():
            # Return empty list if file doesn't exist
            return []
        
        with open(self.policies_file, 'r') as f:
            data = json.load(f)
            return data.get('policies', [])
    
    async def check_policies(self, event_details: Dict[str, Any]) -> List[PolicyViolation]:
        """
        Check all enabled policies against event details.
        
        Args:
            event_details: Dictionary with event information:
                - title: str
                - date: str (YYYY-MM-DD)
                - start_time: str (HH:MM)
                - end_time: str (HH:MM)
                - attendees: str (comma-separated) or List[str]
                - location: str (optional)
        
        Returns:
            List of PolicyViolation objects
        """
        violations = []
        
        for policy in self.policies:
            if not policy.get('enabled', True):
                continue
            
            # Route to appropriate checker based on policy ID
            policy_id = policy.get('id')
            
            if policy_id == 'max_meeting_duration':
                violation = self._check_max_duration(policy, event_details)
            elif policy_id == 'buffer_time':
                violation = self._check_buffer_time(policy, event_details)
            elif policy_id == 'business_hours':
                violation = self._check_business_hours(policy, event_details)
            elif policy_id == 'large_meeting_approval':
                violation = self._check_large_meeting(policy, event_details)
            elif policy_id == 'weekend_scheduling':
                violation = self._check_weekend(policy, event_details)
            elif policy_id == 'late_night_meetings':
                violation = self._check_late_night(policy, event_details)
            elif policy_id == 'early_morning_meetings':
                violation = self._check_early_morning(policy, event_details)
            elif policy_id == 'minimum_attendees':
                violation = self._check_minimum_attendees(policy, event_details)
            else:
                # Unknown policy type
                continue
            
            if violation:
                violations.append(violation)
        
        return violations
    
    def _parse_attendees(self, attendees: Any) -> List[str]:
        """Parse attendees into list of emails"""
        if isinstance(attendees, str):
            return [email.strip() for email in attendees.split(',') if email.strip()]
        elif isinstance(attendees, list):
            return attendees
        return []
    
    def _calculate_duration_hours(self, start_time: str, end_time: str) -> float:
        """Calculate duration in hours between start and end times"""
        start_parts = start_time.split(':')
        end_parts = end_time.split(':')
        
        start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
        end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
        
        duration_minutes = end_minutes - start_minutes
        return duration_minutes / 60.0
    
    def _check_max_duration(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """Check if meeting exceeds maximum duration"""
        max_hours = policy.get('max_hours', 4)
        
        start_time = event.get('start_time')
        end_time = event.get('end_time')
        
        if not start_time or not end_time:
            return None
        
        duration = self._calculate_duration_hours(start_time, end_time)
        
        if duration > max_hours:
            return PolicyViolation(
                policy_id=policy['id'],
                policy_name=policy['name'],
                severity=PolicySeverity(policy['severity']),
                message=policy['message'],
                metadata={'duration_hours': duration, 'max_hours': max_hours}
            )
        
        return None
    
    def _check_buffer_time(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """
        Check if there's sufficient buffer time before/after meeting.
        
        Note: This would require checking adjacent events, which needs calendar access.
        For now, this is a placeholder that returns None.
        """
        # TODO: Implement when calendar access is available
        return None
    
    def _check_business_hours(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """Check if meeting is within business hours"""
        business_start = policy.get('start_time', '09:00')
        business_end = policy.get('end_time', '17:00')
        
        start_time = event.get('start_time')
        end_time = event.get('end_time')
        
        if not start_time or not end_time:
            return None
        
        # Parse times
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        business_start_hour = int(business_start.split(':')[0])
        business_end_hour = int(business_end.split(':')[0])
        
        if start_hour < business_start_hour or end_hour > business_end_hour:
            return PolicyViolation(
                policy_id=policy['id'],
                policy_name=policy['name'],
                severity=PolicySeverity(policy['severity']),
                message=policy['message'],
                metadata={
                    'start_time': start_time,
                    'end_time': end_time,
                    'business_hours': f"{business_start}-{business_end}"
                }
            )
        
        return None
    
    def _check_large_meeting(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """Check if meeting exceeds attendee limit requiring approval"""
        min_attendees = policy.get('min_attendees', 20)
        
        attendees = self._parse_attendees(event.get('attendees', []))
        attendee_count = len(attendees)
        
        if attendee_count >= min_attendees:
            return PolicyViolation(
                policy_id=policy['id'],
                policy_name=policy['name'],
                severity=PolicySeverity(policy['severity']),
                message=policy['message'],
                metadata={
                    'attendee_count': attendee_count,
                    'threshold': min_attendees
                }
            )
        
        return None
    
    def _check_weekend(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """Check if meeting is scheduled on weekend"""
        date_str = event.get('date')
        if not date_str:
            return None
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # 5 = Saturday, 6 = Sunday
            if date_obj.weekday() >= 5:
                return PolicyViolation(
                    policy_id=policy['id'],
                    policy_name=policy['name'],
                    severity=PolicySeverity(policy['severity']),
                    message=policy['message'],
                    metadata={'day_of_week': date_obj.strftime('%A')}
                )
        except ValueError:
            pass
        
        return None
    
    def _check_late_night(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """Check if meeting is scheduled late at night"""
        after_hour = policy.get('after_hour', 20)
        
        start_time = event.get('start_time')
        if not start_time:
            return None
        
        start_hour = int(start_time.split(':')[0])
        
        if start_hour >= after_hour:
            return PolicyViolation(
                policy_id=policy['id'],
                policy_name=policy['name'],
                severity=PolicySeverity(policy['severity']),
                message=policy['message'],
                metadata={'start_hour': start_hour, 'threshold': after_hour}
            )
        
        return None
    
    def _check_early_morning(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """Check if meeting is scheduled very early in the morning"""
        before_hour = policy.get('before_hour', 7)
        
        start_time = event.get('start_time')
        if not start_time:
            return None
        
        start_hour = int(start_time.split(':')[0])
        
        if start_hour < before_hour:
            return PolicyViolation(
                policy_id=policy['id'],
                policy_name=policy['name'],
                severity=PolicySeverity(policy['severity']),
                message=policy['message'],
                metadata={'start_hour': start_hour, 'threshold': before_hour}
            )
        
        return None
    
    def _check_minimum_attendees(self, policy: Dict, event: Dict) -> Optional[PolicyViolation]:
        """Check if meeting has minimum required attendees"""
        min_attendees = policy.get('min_attendees', 2)
        
        attendees = self._parse_attendees(event.get('attendees', []))
        attendee_count = len(attendees)
        
        if attendee_count < min_attendees:
            return PolicyViolation(
                policy_id=policy['id'],
                policy_name=policy['name'],
                severity=PolicySeverity(policy['severity']),
                message=policy['message'],
                metadata={
                    'attendee_count': attendee_count,
                    'minimum': min_attendees
                }
            )
        
        return None
    
    def get_blocking_violations(self, violations: List[PolicyViolation]) -> List[PolicyViolation]:
        """Filter violations to only those that block event creation"""
        return [v for v in violations if v.is_blocking()]
    
    def get_warnings(self, violations: List[PolicyViolation]) -> List[PolicyViolation]:
        """Filter violations to only warnings"""
        return [v for v in violations if v.severity == PolicySeverity.WARNING]
    
    def get_info(self, violations: List[PolicyViolation]) -> List[PolicyViolation]:
        """Filter violations to only informational messages"""
        return [v for v in violations if v.severity == PolicySeverity.INFO]
