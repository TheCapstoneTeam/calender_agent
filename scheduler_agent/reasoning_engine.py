"""
Chain-of-Thought Reasoning Engine

Provides observable reasoning capabilities for agent transparency.
Allows logging, streaming, and analyzing agent decision-making processes.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from collections import defaultdict
import json


class ThoughtType(Enum):
    """Categories of agent reasoning steps"""
    ANALYSIS = "analysis"       # Understanding the request
    PLANNING = "planning"       # Deciding what to do next
    DECISION = "decision"       # Making a specific choice
    CONCERN = "concern"         # Identifying potential issues
    VALIDATION = "validation"   # Checking correctness
    PATTERN = "pattern"         # Recognizing patterns from history
    SUGGESTION = "suggestion"   # Offering recommendations
    WARNING = "warning"         # Flagging important concerns
    RECOMMENDATION = "recommendation"  # Final recommendations


@dataclass
class Thought:
    """A single reasoning step in the chain-of-thought process"""
    content: str
    thought_type: ThoughtType
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thought to dictionary for JSON serialization"""
        return {
            "content": self.content,
            "type": self.thought_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        type_label = f"[{self.thought_type.value.upper()}]"
        return f"{type_label} {self.content}"


class ReasoningEngine:
    """
    Observable reasoning engine for agent transparency.
    
    Usage:
        engine = ReasoningEngine(enabled=True)
        engine.think("User wants to schedule a meeting", ThoughtType.ANALYSIS)
        engine.think("Need to resolve team name to emails", ThoughtType.PLANNING)
        
        # Get all thoughts
        chain = engine.get_reasoning_chain()
        
        # Stream thoughts in real-time
        engine.on_thought(lambda thought: print(thought))
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize reasoning engine.
        
        Args:
            enabled: If False, thoughts are not logged (for production mode)
        """
        self.enabled = enabled
        self.thoughts: List[Thought] = []
        self._listeners: List[Callable[[Thought], None]] = []
    
    def think(
        self, 
        content: str, 
        thought_type: ThoughtType = ThoughtType.ANALYSIS,
        **metadata
    ) -> None:
        """
        Log a reasoning step.
        
        Args:
            content: The thought content
            thought_type: Category of thought
            **metadata: Additional context (e.g., current_date, timezone, user_id)
        
        Example:
            engine.think(
                "User requested 'tomorrow' - resolving to 2025-11-29",
                ThoughtType.ANALYSIS,
                current_date="2025-11-28",
                timezone="Asia/Singapore"
            )
        """
        if not self.enabled:
            return
        
        thought = Thought(
            content=content,
            thought_type=thought_type,
            timestamp=datetime.now(),
            metadata=metadata if metadata else None
        )
        
        self.thoughts.append(thought)
        
        # Notify listeners (for real-time streaming)
        self._emit(thought)
    
    def on_thought(self, listener: Callable[[Thought], None]) -> None:
        """
        Register a listener for real-time thought streaming.
        
        Args:
            listener: Function called when a new thought is logged
        
        Example:
            engine.on_thought(lambda t: print(f"[{t.thought_type.value}] {t.content}"))
        """
        self._listeners.append(listener)
    
    def _emit(self, thought: Thought) -> None:
        """Emit thought to all registered listeners"""
        for listener in self._listeners:
            try:
                listener(thought)
            except Exception as e:
                # Don't let listener errors break reasoning
                print(f"Error in thought listener: {e}")
    
    def get_reasoning_chain(self, thought_type: Optional[ThoughtType] = None) -> List[Thought]:
        """
        Retrieve the chain of thoughts.
        
        Args:
            thought_type: Optional filter for specific thought types
        
        Returns:
            List of thoughts, optionally filtered
        
        Example:
            # Get all concerns
            concerns = engine.get_reasoning_chain(ThoughtType.CONCERN)
        """
        if thought_type is None:
            return self.thoughts.copy()
        
        return [t for t in self.thoughts if t.thought_type == thought_type]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of reasoning including thought counts by type.
        
        Returns:
            Dictionary with summary statistics
        """
        type_counts = defaultdict(int)
        for thought in self.thoughts:
            type_counts[thought.thought_type.value] += 1
        
        return {
            "total_thoughts": len(self.thoughts),
            "thoughts_by_type": dict(type_counts),
            "first_thought": self.thoughts[0].timestamp.isoformat() if self.thoughts else None,
            "last_thought": self.thoughts[-1].timestamp.isoformat() if self.thoughts else None
        }
    
    def to_json(self, pretty: bool = False) -> str:
        """
        Export reasoning chain to JSON.
        
        Args:
            pretty: If True, format with indentation
        
        Returns:
            JSON string of all thoughts
        """
        thoughts_dict = [t.to_dict() for t in self.thoughts]
        indent = 2 if pretty else None
        return json.dumps(thoughts_dict, indent=indent)
    
    def clear(self) -> None:
        """Clear all thoughts (useful for starting a new reasoning session)"""
        self.thoughts.clear()
    
    def __str__(self) -> str:
        """String representation showing all thoughts"""
        if not self.thoughts:
            return "ReasoningEngine: No thoughts logged"
        
        lines = [f"ReasoningEngine: {len(self.thoughts)} thoughts"]
        for thought in self.thoughts:
            lines.append(f"  {thought}")
        return "\n".join(lines)
    
    def __len__(self) -> int:
        """Number of thoughts logged"""
        return len(self.thoughts)
