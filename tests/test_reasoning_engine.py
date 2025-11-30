"""
Tests for the ReasoningEngine module.

Tests cover:
- Basic thought logging
- Thought filtering by type
- JSON serialization
- Real-time streaming
- Reasoning chain retrieval
- Metadata handling
"""

import pytest
import json
from datetime import datetime
from scheduler_agent.reasoning_engine import ReasoningEngine, ThoughtType, Thought


class TestThought:
    """Test the Thought dataclass"""
    
    def test_thought_creation(self):
        """Test creating a thought"""
        thought = Thought(
            content="Test thought",
            thought_type=ThoughtType.ANALYSIS,
            timestamp=datetime.now()
        )
        
        assert thought.content == "Test thought"
        assert thought.thought_type == ThoughtType.ANALYSIS
        assert thought.metadata is None
    
    def test_thought_with_metadata(self):
        """Test creating a thought with metadata"""
        metadata = {"user_id": "123", "session_id": "abc"}
        thought = Thought(
            content="Test thought",
            thought_type=ThoughtType.PLANNING,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        assert thought.metadata == metadata
    
    def test_thought_to_dict(self):
        """Test converting thought to dictionary"""
        timestamp = datetime.now()
        thought = Thought(
            content="Test thought",
            thought_type=ThoughtType.DECISION,
            timestamp=timestamp,
            metadata={"key": "value"}
        )
        
        result = thought.to_dict()
        
        assert result["content"] == "Test thought"
        assert result["type"] == "decision"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["metadata"] == {"key": "value"}
    
    def test_thought_str_representation(self):
        """Test string representation of thought"""
        thought = Thought(
            content="Test content",
            thought_type=ThoughtType.CONCERN,
            timestamp=datetime.now()
        )
        
        result = str(thought)
        
        assert "[CONCERN]" in result
        assert "Test content" in result


class TestReasoningEngine:
    """Test the ReasoningEngine class"""
    
    def test_engine_creation(self):
        """Test creating a reasoning engine"""
        engine = ReasoningEngine(enabled=True)
        
        assert engine.enabled is True
        assert len(engine) == 0
        assert len(engine.thoughts) == 0
    
    def test_think_logs_thought(self):
        """Test that think() logs a thought"""
        engine = ReasoningEngine()
        
        engine.think("Test thought", ThoughtType.ANALYSIS)
        
        assert len(engine) == 1
        assert engine.thoughts[0].content == "Test thought"
        assert engine.thoughts[0].thought_type == ThoughtType.ANALYSIS
    
    def test_think_with_metadata(self):
        """Test logging thought with metadata"""
        engine = ReasoningEngine()
        
        engine.think(
            "Test thought",
            ThoughtType.VALIDATION,
            user_id="123",
            timezone="UTC"
        )
        
        thought = engine.thoughts[0]
        assert thought.metadata == {"user_id": "123", "timezone": "UTC"}
    
    def test_disabled_engine_no_logging(self):
        """Test that disabled engine doesn't log thoughts"""
        engine = ReasoningEngine(enabled=False)
        
        engine.think("This should not be logged", ThoughtType.ANALYSIS)
        
        assert len(engine) == 0
    
    def test_get_reasoning_chain_all(self):
        """Test retrieving all thoughts"""
        engine = ReasoningEngine()
        
        engine.think("Thought 1", ThoughtType.ANALYSIS)
        engine.think("Thought 2", ThoughtType.PLANNING)
        engine.think("Thought 3", ThoughtType.DECISION)
        
        chain = engine.get_reasoning_chain()
        
        assert len(chain) == 3
        assert chain[0].content == "Thought 1"
        assert chain[1].content == "Thought 2"
        assert chain[2].content == "Thought 3"
    
    def test_get_reasoning_chain_filtered(self):
        """Test retrieving thoughts filtered by type"""
        engine = ReasoningEngine()
        
        engine.think("Analysis 1", ThoughtType.ANALYSIS)
        engine.think("Decision 1", ThoughtType.DECISION)
        engine.think("Analysis 2", ThoughtType.ANALYSIS)
        engine.think("Concern 1", ThoughtType.CONCERN)
        engine.think("Analysis 3", ThoughtType.ANALYSIS)
        
        analyses = engine.get_reasoning_chain(ThoughtType.ANALYSIS)
        decisions = engine.get_reasoning_chain(ThoughtType.DECISION)
        concerns = engine.get_reasoning_chain(ThoughtType.CONCERN)
        
        assert len(analyses) == 3
        assert len(decisions) == 1
        assert len(concerns) == 1
        assert all(t.thought_type == ThoughtType.ANALYSIS for t in analyses)
    
    def test_get_summary(self):
        """Test getting reasoning summary"""
        engine = ReasoningEngine()
        
        engine.think("Analysis", ThoughtType.ANALYSIS)
        engine.think("Planning", ThoughtType.PLANNING)
        engine.think("Another analysis", ThoughtType.ANALYSIS)
        engine.think("Decision", ThoughtType.DECISION)
        
        summary = engine.get_summary()
        
        assert summary["total_thoughts"] == 4
        assert summary["thoughts_by_type"]["analysis"] == 2
        assert summary["thoughts_by_type"]["planning"] == 1
        assert summary["thoughts_by_type"]["decision"] == 1
        assert "first_thought" in summary
        assert "last_thought" in summary
    
    def test_to_json(self):
        """Test JSON export"""
        engine = ReasoningEngine()
        
        engine.think("Test thought 1", ThoughtType.ANALYSIS)
        engine.think("Test thought 2", ThoughtType.PLANNING, user="alice")
        
        json_str = engine.to_json()
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        
        assert len(data) == 2
        assert data[0]["content"] == "Test thought 1"
        assert data[0]["type"] == "analysis"
        assert data[1]["content"] == "Test thought 2"
        assert data[1]["metadata"]["user"] == "alice"
    
    def test_to_json_pretty(self):
        """Test pretty JSON export"""
        engine = ReasoningEngine()
        
        engine.think("Test", ThoughtType.ANALYSIS)
        
        json_str = engine.to_json(pretty=True)
        
        # Pretty JSON should have newlines
        assert "\n" in json_str
        assert "  " in json_str  # Indentation
    
    def test_clear(self):
        """Test clearing thoughts"""
        engine = ReasoningEngine()
        
        engine.think("Thought 1", ThoughtType.ANALYSIS)
        engine.think("Thought 2", ThoughtType.PLANNING)
        
        assert len(engine) == 2
        
        engine.clear()
        
        assert len(engine) == 0
        assert len(engine.thoughts) == 0
    
    def test_str_representation(self):
        """Test string representation of engine"""
        engine = ReasoningEngine()
        
        # Empty engine
        result = str(engine)
        assert "No thoughts logged" in result
        
        # Engine with thoughts
        engine.think("Thought 1", ThoughtType.ANALYSIS)
        engine.think("Thought 2", ThoughtType.DECISION)
        
        result = str(engine)
        assert "2 thoughts" in result
        assert "Thought 1" in result
        assert "Thought 2" in result


class TestReasoningEngineStreaming:
    """Test real-time streaming features"""
    
    def test_on_thought_listener(self):
        """Test registering and calling thought listeners"""
        engine = ReasoningEngine()
        
        received_thoughts = []
        
        def capture_thought(thought):
            received_thoughts.append(thought)
        
        engine.on_thought(capture_thought)
        
        engine.think("Test thought", ThoughtType.ANALYSIS)
        
        assert len(received_thoughts) == 1
        assert received_thoughts[0].content == "Test thought"
    
    def test_multiple_listeners(self):
        """Test multiple listeners receive thoughts"""
        engine = ReasoningEngine()
        
        received_1 = []
        received_2 = []
        
        engine.on_thought(lambda t: received_1.append(t))
        engine.on_thought(lambda t: received_2.append(t))
        
        engine.think("Thought 1", ThoughtType.ANALYSIS)
        engine.think("Thought 2", ThoughtType.PLANNING)
        
        assert len(received_1) == 2
        assert len(received_2) == 2
        assert received_1[0].content == "Thought 1"
        assert received_2[1].content == "Thought 2"
    
    def test_listener_exception_handling(self):
        """Test that listener exceptions don't break the engine"""
        engine = ReasoningEngine()
        
        def bad_listener(thought):
            raise ValueError("Listener error")
        
        engine.on_thought(bad_listener)
        
        # This should not raise an exception
        engine.think("Test thought", ThoughtType.ANALYSIS)
        
        # Thought should still be logged
        assert len(engine) == 1


class TestThoughtTypes:
    """Test different thought types"""
    
    def test_all_thought_types(self):
        """Test that all thought types work correctly"""
        engine = ReasoningEngine()
        
        thought_types = [
            ThoughtType.ANALYSIS,
            ThoughtType.PLANNING,
            ThoughtType.DECISION,
            ThoughtType.CONCERN,
            ThoughtType.VALIDATION,
            ThoughtType.PATTERN,
            ThoughtType.SUGGESTION,
            ThoughtType.WARNING,
            ThoughtType.RECOMMENDATION
        ]
        
        for i, thought_type in enumerate(thought_types):
            engine.think(f"Thought {i}", thought_type)
        
        assert len(engine) == len(thought_types)
        
        # Verify each type can be filtered
        for thought_type in thought_types:
            filtered = engine.get_reasoning_chain(thought_type)
            assert len(filtered) == 1
            assert filtered[0].thought_type == thought_type


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    def test_scheduling_workflow(self):
        """Test a complete scheduling workflow with reasoning"""
        engine = ReasoningEngine()
        
        # Simulate scheduling workflow
        engine.think("User wants to schedule meeting", ThoughtType.ANALYSIS)
        engine.think("Parsing date and time", ThoughtType.PLANNING)
        engine.think("Checking team membership", ThoughtType.DECISION)
        engine.think("Found 5 attendees", ThoughtType.VALIDATION)
        engine.think("Checking conflicts", ThoughtType.PLANNING)
        engine.think("Alice has conflict", ThoughtType.CONCERN)
        engine.think("Bob has conflict", ThoughtType.CONCERN)
        engine.think("Finding alternative time", ThoughtType.PLANNING)
        engine.think("All free at 3pm", ThoughtType.VALIDATION)
        engine.think("Suggest 3pm", ThoughtType.RECOMMENDATION)
        
        # Verify workflow
        assert len(engine) == 10
        
        concerns = engine.get_reasoning_chain(ThoughtType.CONCERN)
        assert len(concerns) == 2
        
        recommendations = engine.get_reasoning_chain(ThoughtType.RECOMMENDATION)
        assert len(recommendations) == 1
        assert "3pm" in recommendations[0].content
    
    def test_timezone_scenario(self):
        """Test timezone validation workflow"""
        engine = ReasoningEngine()
        
        engine.think(
            "Converting time to UTC",
            ThoughtType.VALIDATION,
            from_tz="America/New_York",
            to_tz="UTC"
        )
        
        engine.think(
            "Time would be 2am for Singapore attendees",
            ThoughtType.WARNING,
            singapore_time="02:00"
        )
        
        engine.think(
            "Recommend scheduling during overlap hours",
            ThoughtType.RECOMMENDATION
        )
        
        warnings = engine.get_reasoning_chain(ThoughtType.WARNING)
        assert len(warnings) == 1
        assert "2am" in warnings[0].content
