"""
Tests for ADK Sub-Agent Architecture

Verifies that the proper Google ADK sub-agents are configured correctly
with the sub_agents parameter.
"""

import pytest
from scheduler_agent.agent import root_agent
from scheduler_agent.sub_agents import (
    availability_checker_agent,
    event_validator_agent,
    facility_manager_agent,
    event_creator_agent,
)


class TestADKSubAgents:
    """Test ADK sub-agent configuration"""
    
    def test_sub_agents_exist(self):
        """Verify all sub-agents are properly defined as ADK Agents"""
        # Check that they have the ADK Agent attributes
        assert hasattr(availability_checker_agent, 'name')
        assert hasattr(event_validator_agent, 'name')
        assert hasattr(facility_manager_agent, 'name')
        assert hasattr(event_creator_agent, 'name')
        
    def test_sub_agent_names(self):
        """Verify sub-agent names are correct"""
        assert availability_checker_agent.name == "availability_checker"
        assert event_validator_agent.name == "event_validator"
        assert facility_manager_agent.name == "facility_manager"
        assert event_creator_agent.name == "event_creator"
    
    def test_sub_agents_have_tools(self):
        """Verify each sub-agent has appropriate tools"""
        # Availability checker should have tools
        assert hasattr(availability_checker_agent, 'tools')
        assert len(availability_checker_agent.tools) > 0
        
        # Validator should have tools
        assert hasattr(event_validator_agent, 'tools')
        assert len(event_validator_agent.tools) > 0
        
        # Facility manager should have tools
        assert hasattr(facility_manager_agent, 'tools')
        assert len(facility_manager_agent.tools) > 0
        
        # Event creator should have tools
        assert hasattr(event_creator_agent, 'tools')
        assert len(event_creator_agent.tools) > 0
    
    def test_root_agent_has_sub_agents(self):
        """Verify root agent is configured with sub-agents parameter"""
        assert hasattr(root_agent, 'sub_agents')
        assert len(root_agent.sub_agents) == 4
    
    def test_root_agent_sub_agent_names(self):
        """Verify root agent has correct sub-agents"""
        sub_agent_names = [agent.name for agent in root_agent.sub_agents]
        
        assert "availability_checker" in sub_agent_names
        assert "event_validator" in sub_agent_names
        assert "facility_manager" in sub_agent_names
        assert "event_creator" in sub_agent_names
    
    def test_root_agent_has_orchestration_tools(self):
        """Verify root agent has tools for orchestration-level tasks"""
        # Root agent should have tools for coordination tasks (hybrid model)
        assert hasattr(root_agent, 'tools')
        assert len(root_agent.tools) > 0, "Root agent should have orchestration tools"
        
        # Verify it has key orchestration tools
        tool_names = []
        for tool in root_agent.tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
        
        # Should have search tool for holiday checking
        assert any('search' in str(name).lower() for name in tool_names), \
            "Root agent should have search tool for holiday checking"
        
        # Should have user details tool for location/timezone
        assert 'get_user_details' in tool_names, \
            "Root agent should have get_user_details for location detection"
    
    def test_root_agent_name(self):
        """Verify root agent name changed to coordinator"""
        assert root_agent.name == "calendar_coordinator"
    
    def test_sub_agent_instructions_exist(self):
        """Verify all sub-agents have clear instructions"""
        assert availability_checker_agent.instruction is not None
        assert len(availability_checker_agent.instruction) > 100
        
        assert event_validator_agent.instruction is not None
        assert len(event_validator_agent.instruction) > 100
        
        assert facility_manager_agent.instruction is not None
        assert len(facility_manager_agent.instruction) > 100
        
        assert event_creator_agent.instruction is not None
        assert len(event_creator_agent.instruction) > 100


class TestPolicyCheckingTool:
    """Test the policy checking tool used by event_validator"""
    
    def test_check_policies_exists(self):
        """Verify check_policies tool exists"""
        from scheduler_agent.tools.validation import check_policies
        
        assert callable(check_policies)
    
    def test_check_policies_normal_meeting(self):
        """Test policy check for normal meeting"""
        from scheduler_agent.tools.validation import check_policies
        
        result = check_policies(
            duration_hours=1.0,
            attendee_count=5,
            start_hour=10,
            day_of_week="Tuesday"
        )
        
        assert result["allowed"] == True
        assert len(result["violations"]) == 0
    
    def test_check_policies_long_duration(self):
        """Test policy check for long meeting"""
        from scheduler_agent.tools.validation import check_policies
        
        result = check_policies(
            duration_hours=5.0,
            attendee_count=5,
            start_hour=10,
            day_of_week="Tuesday"
        )
        
        assert result["allowed"] == True  # Warning, not violation
        assert len(result["warnings"]) > 0
        assert any("duration" in w.lower() for w in result["warnings"])
    
    def test_check_policies_large_meeting(self):
        """Test policy check for large meeting - SHOULD BLOCK"""
        from scheduler_agent.tools.validation import check_policies
        
        result = check_policies(
            duration_hours=1.0,
            attendee_count=25,
            start_hour=10,
            day_of_week="Tuesday"
        )
        
        assert result["allowed"] == False  # BLOCKED
        assert len(result["violations"]) > 0
        assert any("20+" in v or "approval" in v.lower() for v in result["violations"])
    
    def test_check_policies_outside_business_hours(self):
        """Test policy check for outside business hours"""
        from scheduler_agent.tools.validation import check_policies
        
        result = check_policies(
            duration_hours=1.0,
            attendee_count=5,
            start_hour=20,  # 8 PM
            day_of_week="Tuesday"
        )
        
        assert result["allowed"] == True  # Warning, not block
        assert len(result["warnings"]) > 0
    
    def test_check_policies_weekend(self):
        """Test policy check for weekend meeting"""
        from scheduler_agent.tools.validation import check_policies
        
        result = check_policies(
            duration_hours=1.0,
            attendee_count=5,
            start_hour=10,
            day_of_week="Saturday"
        )
        
        assert result["allowed"] == True  # Warning, not block
        assert len(result["warnings"]) > 0
        assert any("weekend" in w.lower() for w in result["warnings"])


class TestSubAgentIntegration:
    """Test that sub-agents can be imported and used"""
    
    def test_import_all_sub_agents(self):
        """Verify all sub-agents can be imported from package"""
        from scheduler_agent.sub_agents import (
            availability_checker_agent,
            event_validator_agent,
            facility_manager_agent,
            event_creator_agent,
        )
        
        # If we get here without ImportError, test passes
        assert True
    
    def test_import_root_agent(self):
        """Verify root agent can be imported"""
        from scheduler_agent.agent import root_agent
        
        assert root_agent is not None
        assert root_agent.name == "calendar_coordinator"
