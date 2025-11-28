"""
Demonstrates how to integrate ReasoningEngine with the scheduler agent.

This example shows a realistic scheduling workflow with observable reasoning.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheduler_agent.reasoning_engine import ReasoningEngine, ThoughtType
from datetime import datetime, timedelta


class SchedulerWithReasoning:
    """
    Wrapper around the scheduler agent that adds observable reasoning.
    
    This demonstrates how to integrate ReasoningEngine into your agent workflow.
    """
    
    def __init__(self, reasoning_enabled: bool = True):
        self.engine = ReasoningEngine(enabled=reasoning_enabled)
        
        # Add real-time output
        if reasoning_enabled:
            self.engine.on_thought(
                lambda t: print(f"  💭 [{t.thought_type.value.upper()}] {t.content}")
            )
    
    def schedule_meeting(self, user_input: str):
        """
        Schedule a meeting with observable reasoning.
        
        Args:
            user_input: Natural language scheduling request
        """
        print(f"\n{'='*60}")
        print(f"Processing: '{user_input}'")
        print(f"{'='*60}\n")
        
        # Step 1: Parse input
        self.engine.think(
            f"Analyzing user request: '{user_input}'",
            ThoughtType.ANALYSIS
        )
        
        # Simulate parsing
        parsed = self._parse_input(user_input)
        
        self.engine.think(
            f"Extracted: {parsed}",
            ThoughtType.ANALYSIS,
            **parsed
        )
        
        # Step 2: Resolve team to emails
        if "team" in parsed:
            self.engine.think(
                f"Need to resolve team '{parsed['team']}' to email addresses",
                ThoughtType.PLANNING
            )
            
            emails = self._get_team_members(parsed["team"])
            
            self.engine.think(
                f"Found {len(emails)} members in {parsed['team']}",
                ThoughtType.VALIDATION,
                team=parsed["team"],
                members=emails
            )
        else:
            emails = parsed.get("attendees", [])
        
        # Step 3: Check conflicts
        self.engine.think(
            f"Checking availability for {len(emails)} attendees at {parsed['time']}",
            ThoughtType.PLANNING
        )
        
        conflicts = self._check_conflicts(emails, parsed["date"], parsed["time"])
        
        if conflicts:
            self.engine.think(
                f"Found {len(conflicts)} conflicts",
                ThoughtType.CONCERN
            )
            
            for email, conflict_details in conflicts.items():
                self.engine.think(
                    f"{email} has conflict: {conflict_details}",
                    ThoughtType.CONCERN,
                    attendee=email,
                    conflict=conflict_details
                )
            
            # Look for alternatives
            self.engine.think(
                "Searching for alternative time slots",
                ThoughtType.PLANNING
            )
            
            alternative = self._find_alternative_time(emails, parsed["date"])
            
            if alternative:
                self.engine.think(
                    f"All attendees are free at {alternative}",
                    ThoughtType.VALIDATION
                )
                
                self.engine.think(
                    f"Recommend scheduling at {alternative} instead of {parsed['time']}",
                    ThoughtType.RECOMMENDATION,
                    original_time=parsed["time"],
                    suggested_time=alternative
                )
                
                print(f"\n⚠️  Conflicts found! Suggesting {alternative} instead.\n")
            else:
                self.engine.think(
                    "No alternative times found when all attendees are free",
                    ThoughtType.WARNING
                )
                
                print(f"\n❌ Cannot find a suitable time for all attendees.\n")
        else:
            self.engine.think(
                f"No conflicts found - all attendees are available",
                ThoughtType.VALIDATION
            )
            
            self.engine.think(
                f"Creating event on {parsed['date']} at {parsed['time']}",
                ThoughtType.DECISION
            )
            
            print(f"\n✅ Meeting scheduled successfully!\n")
        
        # Show reasoning summary
        print("\n" + "="*60)
        print("REASONING SUMMARY")
        print("="*60)
        summary = self.engine.get_summary()
        print(f"Total thoughts: {summary['total_thoughts']}")
        print(f"Breakdown: {summary['thoughts_by_type']}")
        
        # Show concerns specifically
        concerns = self.engine.get_reasoning_chain(ThoughtType.CONCERN)
        if concerns:
            print(f"\nConcerns identified: {len(concerns)}")
            for c in concerns:
                print(f"  - {c.content}")
    
    def _parse_input(self, user_input: str) -> dict:
        """Simulate parsing user input"""
        # Simple simulation - in real implementation, use LLM or parser
        if "tomorrow" in user_input.lower():
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date = "2025-11-29"
        
        if "2pm" in user_input.lower():
            time = "14:00"
        elif "3pm" in user_input.lower():
            time = "15:00"
        else:
            time = "14:00"
        
        if "teamella" in user_input.lower():
            return {"date": date, "time": time, "team": "TeamElla"}
        else:
            return {"date": date, "time": time, "attendees": ["alice@example.com"]}
    
    def _get_team_members(self, team_name: str) -> list:
        """Simulate getting team members"""
        # Simulated team data
        teams = {
            "TeamElla": [
                "alice@example.com",
                "bob@example.com",
                "carol@example.com",
                "dave@example.com",
                "eve@example.com"
            ]
        }
        return teams.get(team_name, [])
    
    def _check_conflicts(self, emails: list, date: str, time: str) -> dict:
        """Simulate checking for conflicts"""
        # Simulate that Alice and Bob have conflicts at 2pm
        if time == "14:00":
            return {
                "alice@example.com": "Existing meeting 14:00-15:00",
                "bob@example.com": "Existing meeting 14:00-14:30"
            }
        return {}
    
    def _find_alternative_time(self, emails: list, date: str) -> str:
        """Simulate finding alternative time"""
        # Simulate that 3pm works for everyone
        return "15:00"


def demo_successful_scheduling():
    """Demo: Successful scheduling with no conflicts"""
    scheduler = SchedulerWithReasoning(reasoning_enabled=True)
    scheduler.schedule_meeting("Schedule a meeting tomorrow at 3pm with TeamElla")


def demo_conflict_resolution():
    """Demo: Scheduling with conflicts and alternative suggestion"""
    scheduler = SchedulerWithReasoning(reasoning_enabled=True)
    scheduler.schedule_meeting("Schedule a meeting tomorrow at 2pm with TeamElla")


def demo_without_reasoning():
    """Demo: Same workflow but without reasoning (silent mode)"""
    print("\n" + "="*60)
    print("DEMO: Silent Mode (Reasoning Disabled)")
    print("="*60)
    
    scheduler = SchedulerWithReasoning(reasoning_enabled=False)
    
    print("\nProcessing: 'Schedule a meeting tomorrow at 2pm with TeamElla'")
    print("(No reasoning output - agent works silently)\n")
    
    # Even with reasoning disabled, the logic still works
    print("✅ Meeting scheduled (reasoning was disabled)")


def main():
    """Run all scheduler reasoning demos"""
    print("\n" + "🧠 SCHEDULER WITH CHAIN-OF-THOUGHT REASONING 🧠".center(60))
    
    demo_successful_scheduling()
    
    print("\n" + "-"*60 + "\n")
    
    demo_conflict_resolution()
    
    print("\n" + "-"*60 + "\n")
    
    demo_without_reasoning()
    
    print("\n" + "="*60)
    print("All scheduler demos completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
