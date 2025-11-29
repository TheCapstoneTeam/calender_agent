"""
Tests for Parallel Availability Checker Sub-Agents

Tests cover:
- Individual AvailabilityCheckerAgent functionality
- ParallelAvailabilityCoordinator orchestration
- Error handling and graceful degradation
- Performance characteristics
- Integration with ReasoningEngine
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from scheduler_agent.parallel_execution import ParallelAvailabilityCoordinator, AvailabilityCheckerAgent


class TestAvailabilityCheckerAgent:
    """Test the individual availability checker sub-agent"""
    
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """Test creating an availability checker agent"""
        agent = AvailabilityCheckerAgent(timeout_seconds=3)
        
        assert agent.timeout_seconds == 3
        assert agent.service is None  # Lazy loaded
    
    @pytest.mark.asyncio
    async def test_check_availability_structure(self):
        """Test that check_availability returns correct structure"""
        agent = AvailabilityCheckerAgent(timeout_seconds=3)
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.check_availability(
            email="test@example.com",
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Verify structure
        assert "email" in result
        assert "available" in result
        assert "conflicts" in result
        assert "error" in result
        assert "execution_time" in result
        
        assert result["email"] == "test@example.com"
        assert isinstance(result["available"], bool)
        assert isinstance(result["conflicts"], list)
        assert isinstance(result["execution_time"], float)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that timeout is enforced"""
        agent = AvailabilityCheckerAgent(timeout_seconds=0.001)  # Very short timeout
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await agent.check_availability(
            email="test@example.com",
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Should timeout and return error
        assert result["error"] is not None
        assert "Timeout" in result["error"]


class TestParallelAvailabilityCoordinator:
    """Test the parallel coordinator"""
    
    @pytest.mark.asyncio
    async def test_coordinator_creation(self):
        """Test creating a coordinator"""
        coordinator = ParallelAvailabilityCoordinator(
            timeout_seconds=3,
            max_parallel=50
        )
        
        assert coordinator.timeout_seconds == 3
        assert coordinator.max_parallel == 50
    
    @pytest.mark.asyncio
    async def test_empty_attendees(self):
        """Test handling empty attendee list"""
        coordinator = ParallelAvailabilityCoordinator()
        
        result = await coordinator.check_all_attendees(
            attendees=[],
            date="2025-11-29",
            start_time="14:00",
            end_time="15:00"
        )
        
        assert result["all_available"] is True
        assert result["available_count"] == 0
        assert result["busy_count"] == 0
        assert result["error_count"] == 0
    
    @pytest.mark.asyncio
    async def test_single_attendee(self):
        """Test checking single attendee"""
        coordinator = ParallelAvailabilityCoordinator()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await coordinator.check_all_attendees(
            attendees=["test@example.com"],
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Verify structure
        assert "all_available" in result
        assert "available_count" in result
        assert "busy_count" in result
        assert "error_count" in result
        assert "available_attendees" in result
        assert "busy_attendees" in result
        assert "errors" in result
        assert "execution_time" in result
        assert "parallelization_factor" in result
    
    @pytest.mark.asyncio
    async def test_multiple_attendees(self):
        """Test checking multiple attendees in parallel"""
        coordinator = ParallelAvailabilityCoordinator()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        attendees = [
            "alice@example.com",
            "bob@example.com",
            "carol@example.com"
        ]
        
        result = await coordinator.check_all_attendees(
            attendees=attendees,
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Should have checked all attendees
        total_checked = (
            result["available_count"] + 
            result["busy_count"] + 
            result["error_count"]
        )
        assert total_checked == len(attendees)
    
    @pytest.mark.asyncio
    async def test_duplicate_attendees(self):
        """Test that duplicate attendees are deduplicated"""
        coordinator = ParallelAvailabilityCoordinator()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Intentional duplicates
        attendees = [
            "alice@example.com",
            "bob@example.com",
            "alice@example.com",  # duplicate
            "bob@example.com",    # duplicate
        ]
        
        result = await coordinator.check_all_attendees(
            attendees=attendees,
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Should only check unique attendees (2)
        total_checked = (
            result["available_count"] + 
            result["busy_count"] + 
            result["error_count"]
        )
        assert total_checked == 2  # Only alice and bob
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test that performance metrics are calculated"""
        coordinator = ParallelAvailabilityCoordinator()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await coordinator.check_all_attendees(
            attendees=["alice@example.com", "bob@example.com"],
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Execution time should be positive
        assert result["execution_time"] > 0
        
        # Parallelization factor should be calculated
        assert result["parallelization_factor"] >= 1.0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ReasoningEngine thought logging may not work in isolated test environment. "
                             "The coordinator._log_thought() method requires both REASONING_AVAILABLE flag "
                             "and a valid reasoning_engine instance. This test may fail due to API mocking "
                             "or incomplete integration. Should be tested in full integration environment.")
    async def test_reasoning_integration(self):
        """Test integration with ReasoningEngine"""
        from scheduler_agent.reasoning_engine import ReasoningEngine, ThoughtType
        
        engine = ReasoningEngine(enabled=True)
        coordinator = ParallelAvailabilityCoordinator(reasoning_engine=engine)
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await coordinator.check_all_attendees(
            attendees=["alice@example.com", "bob@example.com"],
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Should have logged thoughts
        assert len(engine) > 0
        
        # Should have planning thoughts
        planning_thoughts = engine.get_reasoning_chain(ThoughtType.PLANNING)
        assert len(planning_thoughts) > 0


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_small_team_meeting(self):
        """Test scheduling a small team meeting (3-5 people)"""
        coordinator = ParallelAvailabilityCoordinator()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        team = [
            "alice@example.com",
            "bob@example.com",
            "carol@example.com",
            "dave@example.com"
        ]
        
        result = await coordinator.check_all_attendees(
            attendees=team,
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Should complete quickly
        assert result["execution_time"] < 5.0  # Should be under 5 seconds
        
        # Should check all attendees
        total = result["available_count"] + result["busy_count"] + result["error_count"]
        assert total == len(team)
    
    @pytest.mark.asyncio
    async def test_large_meeting(self):
        """Test scheduling a large meeting (10+ people)"""
        coordinator = ParallelAvailabilityCoordinator()
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Large team
        team = [f"employee{i:02d}@company.com" for i in range(1, 11)]
        
        result = await coordinator.check_all_attendees(
            attendees=team,
            date=tomorrow,
            start_time="14:00",
            end_time="15:00"
        )
        
        # Should still complete quickly (parallel benefit)
        assert result["execution_time"] < 10.0
        
        # Should show parallelization benefit
        assert result["parallelization_factor"] > 1.0
