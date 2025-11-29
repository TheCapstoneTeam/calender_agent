"""
Tests for Stage 2: Conflict Detection & Validation

Tests cover:
- PolicyEngine loading and rule checking
- ConflictValidationAgent multi-dimensional validation
- Integration with ReasoningEngine
- Various policy violation scenarios
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from scheduler_agent.tools.validation import validate_event_comprehensive, check_policies
from scheduler_agent.parallel_execution.policy_engine import PolicyEngine, PolicyViolation, PolicySeverity
from scheduler_agent.parallel_execution.validation_agent import ConflictValidationAgent, ValidationDimension, ValidationResult


class TestPolicyEngine:
    """Test the Policy Engine"""
    
    @pytest.mark.asyncio
    async def test_load_policies(self):
        """Test loading policies from JSON"""
        engine = PolicyEngine()
        
        assert len(engine.policies) > 0
        assert any(p['id'] == 'max_meeting_duration' for p in engine.policies)
        assert any(p['id'] == 'large_meeting_approval' for p in engine.policies)
    
    @pytest.mark.asyncio
    async def test_max_duration_violation(self):
        """Test meeting duration policy"""
        engine = PolicyEngine()
        
        # 5-hour meeting (exceeds 4-hour limit)
        violations = await engine.check_policies({
            "title": "Long Meeting",
            "date": "2025-11-30",
            "start_time": "09:00",
            "end_time": "14:00",  # 5 hours
            "attendees": "alice@example.com"
        })
        
        duration_violations = [v for v in violations if v.policy_id == 'max_meeting_duration']
        assert len(duration_violations) > 0
        assert duration_violations[0].severity == PolicySeverity.WARNING
    
    @pytest.mark.asyncio
    async def test_large_meeting_approval(self):
        """Test large meeting policy (20+ attendees)"""
        engine = PolicyEngine()
        
        # 25 attendees (requires approval)
        large_team = [f"person{i}@company.com" for i in range(25)]
        
        violations = await engine.check_policies({
            "title": "All Hands",
            "date": "2025-11-30",
            "start_time": "14:00",
            "end_time": "15:00",
            "attendees": large_team
        })
        
        approval_violations = [v for v in violations if v.policy_id == 'large_meeting_approval']
        assert len(approval_violations) > 0
        assert approval_violations[0].severity == PolicySeverity.ERROR
        assert approval_violations[0].is_blocking()
    
    @pytest.mark.asyncio
    async def test_business_hours_violation(self):
        """Test business hours policy"""
        engine = PolicyEngine()
        
        # Meeting at 8 PM (outside 9-5)
        violations = await engine.check_policies({
            "title": "Late Meeting",
            "date": "2025-11-30",
            "start_time": "20:00",
            "end_time": "21:00",
            "attendees": "alice@example.com"
        })
        
        business_violations = [v for v in violations if v.policy_id == 'business_hours']
        assert len(business_violations) > 0
    
    @pytest.mark.asyncio
    async def test_weekend_violation(self):
        """Test weekend scheduling policy"""
        engine = PolicyEngine()
        
        # Find next Saturday
        today = datetime.now()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        next_saturday = (today + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")
        
        violations = await engine.check_policies({
            "title": "Weekend Meeting",
            "date": next_saturday,
            "start_time": "10:00",
            "end_time": "11:00",
            "attendees": "alice@example.com"
        })
        
        weekend_violations = [v for v in violations if v.policy_id == 'weekend_scheduling']
        assert len(weekend_violations) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_violations(self):
        """Test event with multiple policy violations"""
        engine = PolicyEngine()
        
        # Long meeting outside business hours on weekend
        today = datetime.now()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        next_saturday = (today + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")
        
        violations = await engine.check_policies({
            "title": "Weekend Marathon",
            "date": next_saturday,
            "start_time": "08:00",
            "end_time": "18:00",  # 10 hours, before 9 AM, after 5 PM
            "attendees": "alice@example.com"
        })
        
        # Should have multiple violations
        assert len(violations) >= 2


class TestConflictValidationAgent:
    """Test the Conflict Validation Agent"""
    
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """Test creating validation agent"""
        agent = ConflictValidationAgent()
        
        assert agent.policy_engine is not None
    
    @pytest.mark.asyncio
    async def test_validate_structure(self):
        """Test that validate_event returns correct structure"""
        agent = ConflictValidationAgent()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.validate_event({
            "title": "Test Meeting",
            "date": tomorrow,
            "start_time": "14:00",
            "end_time": "15:00",
            "attendees": "alice@example.com"
        })
        
        # Verify structure
        assert "valid" in result
        assert "blocking_issues" in result
        assert "warnings" in result
        assert "validations" in result
        assert "execution_time" in result
        
        assert isinstance(result["valid"], bool)
        assert isinstance(result["blocking_issues"], list)
        assert isinstance(result["warnings"], list)
        assert isinstance(result["execution_time"], float)
    
    @pytest.mark.asyncio
    async def test_valid_event(self):
        """Test validation of a simple valid event"""
        agent = ConflictValidationAgent()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.validate_event({
            "title": "Team Standup",
            "date": tomorrow,
            "start_time": "10:00",
            "end_time": "10:30",
            "attendees": "alice@example.com, bob@example.com",
            "location": "Meeting Room A"
        })
        
        # Should be valid (no blocking issues)
        # May have warnings, but should be valid
        assert result["valid"] or len(result["blocking_issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_large_meeting_blocked(self):
        """Test that large meetings are blocked"""
        agent = ConflictValidationAgent()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        large_team = [f"person{i}@company.com" for i in range(25)]
        
        result = await agent.validate_event({
            "title": "All Hands",
            "date": tomorrow,
            "start_time": "14:00",
            "end_time": "15:00",
            "attendees": ",".join(large_team)
        })
        
        # Should be invalid due to large meeting policy
        assert not result["valid"]
        assert len(result["blocking_issues"]) > 0
    
    @pytest.mark.asyncio
    async def test_parallel_validation(self):
        """Test that validations run in parallel"""
        agent = ConflictValidationAgent()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.validate_event({
            "title": "Team Meeting",
            "date": tomorrow,
            "start_time": "14:00",
            "end_time": "15:00",
            "attendees": "alice@example.com"
        })
        
        # Should have results from all 4 validation dimensions
        assert len(result["validations"]) == 4
        
        # Verify all dimensions present
        dimensions = set(result["validations"].keys())
        expected = {
            ValidationDimension.CALENDAR_CONFLICTS,
            ValidationDimension.ROOM_AVAILABILITY,
            ValidationDimension.TIMEZONE_VIOLATIONS,
            ValidationDimension.POLICY_VIOLATIONS
        }
        assert dimensions == expected
    
    @pytest.mark.asyncio
    async def test_reasoning_integration(self):
        """Test integration with ReasoningEngine"""
        from scheduler_agent.reasoning_engine import ReasoningEngine, ThoughtType
        
        engine = ReasoningEngine(enabled=True)
        agent = ConflictValidationAgent(reasoning_engine=engine)
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.validate_event({
            "title": "Team Meeting",
            "date": tomorrow,
            "start_time": "14:00",
            "end_time": "15:00",
            "attendees": "alice@example.com"
        })
        
        # Should have logged thoughts
        assert len(engine) > 0
        
        # Should have planning thoughts
        planning_thoughts = engine.get_reasoning_chain(ThoughtType.PLANNING)
        assert len(planning_thoughts) > 0


class TestIntegrationScenarios:
    """Test realistic validation scenarios"""
    
    @pytest.mark.asyncio
    async def test_typical_team_meeting(self):
        """Test validating a typical team meeting"""
        agent = ConflictValidationAgent()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.validate_event({
            "title": "Sprint Planning",
            "date": tomorrow,
            "start_time": "10:00",
            "end_time": "12:00",  # 2 hours - OK
            "attendees": "alice@example.com, bob@example.com, carol@example.com, dave@example.com",
            "location": "Conference Room"
        })
        
        # Should be valid
        assert result["execution_time"] > 0
    
    @pytest.mark.asyncio
    async def test_problematic_event(self):
        """Test event with multiple problems"""
        agent = ConflictValidationAgent()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        large_team = [f"person{i}@company.com" for i in range(30)]
        
        result = await agent.validate_event({
            "title": "Marathon Planning",
            "date": tomorrow,
            "start_time": "08:00",
            "end_time": "20:00",  # 12 hours!
            "attendees": ",".join(large_team)  # 30 people!
        })
        
        # Should have multiple issues/warnings
        total_problems = len(result["blocking_issues"]) + len(result["warnings"])
        assert total_problems >= 2
    
    @pytest.mark.asyncio
    async def test_performance_under_2_seconds(self):
        """Test that validation completes quickly"""
        agent = ConflictValidationAgent()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.validate_event({
            "title": "Quick Test",
            "date": tomorrow,
            "start_time": "14:00",
            "end_time": "15:00",
            "attendees": ",".join([f"p{i}@company.com" for i in range(5)])
        })
        
        # Should complete in under 2 seconds (parallel execution)
        assert result["execution_time"] < 2.0
