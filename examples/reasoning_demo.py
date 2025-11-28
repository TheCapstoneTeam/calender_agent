"""
Basic demonstration of the ReasoningEngine.

This example shows how to:
1. Create a reasoning engine
2. Log different types of thoughts
3. Stream thoughts in real-time
4. Export to JSON
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheduler_agent.reasoning_engine import ReasoningEngine, ThoughtType


def basic_usage_demo():
    """Demonstrate basic reasoning engine features"""
    print("=" * 60)
    print("BASIC USAGE DEMO")
    print("=" * 60)
    
    # Create reasoning engine
    engine = ReasoningEngine(enabled=True)
    
    # Log different types of thoughts
    engine.think("User wants to schedule a meeting", ThoughtType.ANALYSIS)
    engine.think("Need to parse date and time from input", ThoughtType.PLANNING)
    engine.think("Calling get_team_members to resolve attendees", ThoughtType.DECISION)
    engine.think("Found 5 members in TeamElla", ThoughtType.ANALYSIS)
    engine.think("Alice has a conflict at requested time", ThoughtType.CONCERN)
    engine.think("All other attendees are free at 3pm", ThoughtType.VALIDATION)
    engine.think("Suggesting 3pm as alternative", ThoughtType.RECOMMENDATION)
    
    # Display reasoning chain
    print("\nReasoning Chain:")
    print(engine)
    
    # Get summary
    print("\nSummary:")
    summary = engine.get_summary()
    print(f"  Total thoughts: {summary['total_thoughts']}")
    print(f"  Thoughts by type: {summary['thoughts_by_type']}")
    
    print()


def filtered_retrieval_demo():
    """Demonstrate filtering thoughts by type"""
    print("=" * 60)
    print("FILTERED RETRIEVAL DEMO")
    print("=" * 60)
    
    engine = ReasoningEngine()
    
    # Simulate a scheduling workflow
    engine.think("User requested meeting for tomorrow at 2pm", ThoughtType.ANALYSIS)
    engine.think("Tomorrow is 2025-11-29", ThoughtType.VALIDATION)
    engine.think("Need to check availability for all attendees", ThoughtType.PLANNING)
    engine.think("Bob has a conflict from 2pm-2:30pm", ThoughtType.CONCERN)
    engine.think("Alice has a conflict from 2pm-3pm", ThoughtType.CONCERN)
    engine.think("Meeting duration is 1 hour, so 2pm won't work", ThoughtType.ANALYSIS)
    engine.think("Checking alternative time: 3pm", ThoughtType.PLANNING)
    engine.think("All attendees free at 3pm", ThoughtType.VALIDATION)
    engine.think("Recommend scheduling at 3pm instead", ThoughtType.RECOMMENDATION)
    
    # Get only concerns
    print("\nAll Concerns:")
    concerns = engine.get_reasoning_chain(ThoughtType.CONCERN)
    for concern in concerns:
        print(f"  - {concern.content}")
    
    # Get only recommendations
    print("\nAll Recommendations:")
    recommendations = engine.get_reasoning_chain(ThoughtType.RECOMMENDATION)
    for rec in recommendations:
        print(f"  - {rec.content}")
    
    print()


def real_time_streaming_demo():
    """Demonstrate real-time thought streaming"""
    print("=" * 60)
    print("REAL-TIME STREAMING DEMO")
    print("=" * 60)
    
    # Create engine with listener
    engine = ReasoningEngine()
    
    # Add a listener that prints thoughts as they occur
    def print_thought(thought):
        print(f"  💭 [{thought.thought_type.value.upper():12}] {thought.content}")
    
    engine.on_thought(print_thought)
    
    print("\nSimulating agent reasoning (thoughts printed in real-time):\n")
    
    # These will be printed immediately as they're logged
    engine.think("Parsing user input", ThoughtType.ANALYSIS)
    engine.think("Extracted: date=tomorrow, time=2pm, team=TeamElla", ThoughtType.ANALYSIS)
    engine.think("Resolving 'TeamElla' to email addresses", ThoughtType.PLANNING)
    engine.think("Found 5 team members", ThoughtType.VALIDATION)
    engine.think("Checking calendar conflicts for all 5 members", ThoughtType.PLANNING)
    engine.think("2 conflicts found", ThoughtType.CONCERN)
    engine.think("Analyzing alternative time slots", ThoughtType.PLANNING)
    engine.think("3pm works for all attendees", ThoughtType.VALIDATION)
    engine.think("Suggest 3pm as the meeting time", ThoughtType.RECOMMENDATION)
    
    print()


def json_export_demo():
    """Demonstrate JSON export functionality"""
    print("=" * 60)
    print("JSON EXPORT DEMO")
    print("=" * 60)
    
    engine = ReasoningEngine()
    
    engine.think(
        "User requested 'tomorrow' - resolving to 2025-11-29",
        ThoughtType.ANALYSIS,
        current_date="2025-11-28",
        timezone="Asia/Singapore"
    )
    engine.think(
        "Time '2pm' converts to 14:00 in 24-hour format",
        ThoughtType.VALIDATION
    )
    engine.think(
        "Checking if 2025-11-29 14:00 is within business hours",
        ThoughtType.VALIDATION,
        business_hours="09:00-17:00"
    )
    
    # Export to JSON
    print("\nJSON Export:")
    json_output = engine.to_json(pretty=True)
    print(json_output)
    
    print()


def metadata_usage_demo():
    """Demonstrate using metadata for rich context"""
    print("=" * 60)
    print("METADATA USAGE DEMO")
    print("=" * 60)
    
    engine = ReasoningEngine()
    
    # Add thoughts with rich metadata
    engine.think(
        "Converting timezone from user input",
        ThoughtType.VALIDATION,
        from_timezone="America/New_York",
        to_timezone="Asia/Singapore",
        original_time="2pm",
        converted_time="2am next day"
    )
    
    engine.think(
        "This would be outside business hours for Singapore",
        ThoughtType.WARNING,
        singapore_time="02:00",
        business_hours="09:00-17:00"
    )
    
    # Show thoughts with metadata
    print("\nThoughts with metadata:")
    for thought in engine.get_reasoning_chain():
        print(f"\n  {thought}")
        if thought.metadata:
            print(f"    Metadata: {thought.metadata}")
    
    print()


def main():
    """Run all demonstrations"""
    basic_usage_demo()
    filtered_retrieval_demo()
    real_time_streaming_demo()
    json_export_demo()
    metadata_usage_demo()
    
    print("=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
