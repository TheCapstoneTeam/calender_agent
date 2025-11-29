"""
Parallel coordinator for managing multiple availability checker sub-agents.

This coordinator spawns multiple AvailabilityCheckerAgent instances and runs
them in parallel to dramatically speed up multi-attendee availability checking.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from .availability_checker import AvailabilityCheckerAgent

# Optional integration with ReasoningEngine
try:
    from ..reasoning_engine import ReasoningEngine, ThoughtType
    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False
    ReasoningEngine = None
    ThoughtType = None


class ParallelAvailabilityCoordinator:
    """
    Coordinates multiple AvailabilityChecker sub-agents  to check attendee
    availability in parallel.
    
    Performance: Checking N attendees takes approximately the same time as
    checking 1 attendee (with appropriate hardware/network capacity).
    
    Usage:
        coordinator = ParallelAvailabilityCoordinator()
        result = await coordinator.check_all_attendees(
            attendees=["alice@example.com", "bob@example.com", "carol@example.com"],
            date="2025-11-29",
            start_time="14:00",
            end_time="15:00"
        )
    """
    
    def __init__(
        self,
        timeout_seconds: int = 3,
        max_parallel: int = 50,
        reasoning_engine: Optional['ReasoningEngine'] = None
    ):
        """
        Initialize the parallel availability coordinator.
        
        Args:
            timeout_seconds: Maximum time to wait per attendee
            max_parallel: Maximum number of parallel checks (safety limit)
            reasoning_engine: Optional ReasoningEngine for observable reasoning
        """
        self.timeout_seconds = timeout_seconds
        self.max_parallel = max_parallel
        self.reasoning_engine = reasoning_engine
    
    def _log_thought(self, content: str, thought_type=None):
        """Log a thought if reasoning engine is available"""
        if self.reasoning_engine and REASONING_AVAILABLE:
            if thought_type is None:
                thought_type = ThoughtType.PLANNING
            self.reasoning_engine.think(content, thought_type)
    
    async def check_all_attendees(
        self,
        attendees: List[str],
        date: str,
        start_time: str,
        end_time: str,
        timezone: str = None
    ) -> Dict[str, Any]:
        """
        Check availability for all attendees in parallel.
        
        Args:
            attendees: List of attendee email addresses
            date: Date string (DD-MM-YYYY or YYYY-MM-DD)
            start_time: Start time "HH:MM"
            end_time: End time "HH:MM" or duration "2hr"
            timezone: Timezone name. If None, uses system timezone
        
        Returns:
            {
                "all_available": bool,
                "available_count": int,
                "busy_count": int,
                "error_count": int,
                "available_attendees": [emails],
                "busy_attendees": {email: [conflicts]},
                "errors": {email: error_msg},
                "execution_time": float,
                "parallelization_factor": float  # speedup vs sequential
            }
        """
        start_time_exec = datetime.now()
        
        # Validate inputs
        if not attendees:
            return {
                "all_available": True,
                "available_count": 0,
                "busy_count": 0,
                "error_count": 0,
                "available_attendees": [],
                "busy_attendees": {},
                "errors": {},
                "execution_time": 0.0,
                "parallelization_factor": 1.0
            }
        
        # Clean and deduplicate attendees
        attendees = [email.strip() for email in attendees if email.strip()]
        attendees = list(set(attendees))  # Remove duplicates
        
        num_attendees = len(attendees)
        
        # Log reasoning
        self._log_thought(
            f"Checking availability for {num_attendees} attendees in parallel",
            ThoughtType.PLANNING if REASONING_AVAILABLE else None
        )
        
        # Cap parallel execution for safety
        if num_attendees > self.max_parallel:
            self._log_thought(
                f"Capping parallel execution at {self.max_parallel} (requested {num_attendees})",
                ThoughtType.WARNING if REASONING_AVAILABLE else None
            )
            # Process in batches
            return await self._check_in_batches(
                attendees, date, start_time, end_time, timezone
            )
        
        self._log_thought(
            f"Spawning {num_attendees} AvailabilityChecker sub-agents",
            ThoughtType.DECISION if REASONING_AVAILABLE else None
        )
        
        # Create sub-agents
        agents = [
            AvailabilityCheckerAgent(timeout_seconds=self.timeout_seconds)
            for _ in attendees
        ]
        
        #Create tasks for parallel execution
        tasks = [
            agent.check_availability(email, date, start_time, end_time, timezone)
            for agent, email in zip(agents, attendees)
        ]
        
        # Run all checks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        available_attendees = []
        busy_attendees = {}
        errors = {}
        
        for result in results:
            # Handle exceptions
            if isinstance(result, Exception):
                email = "unknown"
                errors[email] = str(result)
                self._log_thought(
                    f"Sub-agent exception: {str(result)}",
                    ThoughtType.CONCERN if REASONING_AVAILABLE else None
                )
                continue
            
            email = result["email"]
            
            if result["error"]:
                errors[email] = result["error"]
                self._log_thought(
                    f"{email}: Error - {result['error']}",
                    ThoughtType.CONCERN if REASONING_AVAILABLE else None
                )
            elif result["available"]:
                available_attendees.append(email)
                self._log_thought(
                    f"{email}: Available",
                    ThoughtType.VALIDATION if REASONING_AVAILABLE else None
                )
            else:
                busy_attendees[email] = result["conflicts"]
                self._log_thought(
                    f"{email}: Busy ({len(result['conflicts'])} conflict(s))",
                    ThoughtType.CONCERN if REASONING_AVAILABLE else None
                )
        
        # Calculate metrics
        execution_time = (datetime.now() - start_time_exec).total_seconds()
        available_count = len(available_attendees)
        busy_count = len(busy_attendees)
        error_count = len(errors)
        all_available = (busy_count == 0 and error_count == 0)
        
        # Estimate parallelization speedup
        # Assume sequential would take ~1 second per attendee
        estimated_sequential_time = num_attendees * 1.0
        parallelization_factor = estimated_sequential_time / execution_time if execution_time > 0 else 1.0
        
        self._log_thought(
            f"Results: {available_count} available, {busy_count} busy, {error_count} errors "
            f"(completed in {execution_time:.2f}s, ~{parallelization_factor:.1f}x speedup)",
            ThoughtType.ANALYSIS if REASONING_AVAILABLE else None
        )
        
        return {
            "all_available": all_available,
            "available_count": available_count,
            "busy_count": busy_count,
            "error_count": error_count,
            "available_attendees": available_attendees,
            "busy_attendees": busy_attendees,
            "errors": errors,
            "execution_time": execution_time,
            "parallelization_factor": parallelization_factor
        }
    
    async def _check_in_batches(
        self,
        attendees: List[str],
        date: str,
        start_time: str,
        end_time: str,
        timezone: str = None
    ) -> Dict[str, Any]:
        """
        Check attendees in batches when number exceeds max_parallel.
        
        This prevents overwhelming the system with too many concurrent requests.
        """
        all_results = {
            "all_available": True,
            "available_count": 0,
            "busy_count": 0,
            "error_count": 0,
            "available_attendees": [],
            "busy_attendees": {},
            "errors": {},
            "execution_time": 0.0,
            "parallelization_factor": 1.0
        }
        
        start_time_exec = datetime.now()
        
        # Process in batches
        for i in range(0, len(attendees), self.max_parallel):
            batch = attendees[i:i + self.max_parallel]
            
            self._log_thought(
                f"Processing batch {i//self.max_parallel + 1} ({len(batch)} attendees)",
                ThoughtType.PLANNING if REASONING_AVAILABLE else None
            )
            
            # Create temporary coordinator for this batch
            batch_coordinator = ParallelAvailabilityCoordinator(
                timeout_seconds=self.timeout_seconds,
                max_parallel=self.max_parallel,
                reasoning_engine=None  # Avoid duplicate logging
            )
            
            batch_result = await batch_coordinator.check_all_attendees(
                batch, date, start_time, end_time, timezone
            )
            
            # Merge results
            all_results["available_count"] += batch_result["available_count"]
            all_results["busy_count"] += batch_result["busy_count"]
            all_results["error_count"] += batch_result["error_count"]
            all_results["available_attendees"].extend(batch_result["available_attendees"])
            all_results["busy_attendees"].update(batch_result["busy_attendees"])
            all_results["errors"].update(batch_result["errors"])
        
        all_results["all_available"] = (
            all_results["busy_count"] == 0 and all_results["error_count"] == 0
        )
        all_results["execution_time"] = (datetime.now() - start_time_exec).total_seconds()
        
        # Calculate parallelization factor
        estimated_sequential = len(attendees) * 1.0
        all_results["parallelization_factor"] = (
            estimated_sequential / all_results["execution_time"]
            if all_results["execution_time"] > 0 else 1.0
        )
        
        return all_results
