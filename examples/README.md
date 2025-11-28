# Examples

This directory contains demonstration scripts for various features of the calendar agent.

## Chain-of-Thought Reasoning

### `reasoning_demo.py`

Demonstrates the core features of the ReasoningEngine module:

- **Basic Usage**: Creating an engine and logging thoughts
- **Filtered Retrieval**: Getting specific types of thoughts (concerns, recommendations, etc.)
- **Real-Time Streaming**: Live output as the agent thinks
- **JSON Export**: Exporting reasoning chains for analysis
- **Metadata**: Adding contextual information to thoughts

**Run it:**
```bash
python examples/reasoning_demo.py
```

### `scheduler_reasoning_demo.py`

Shows how to integrate ReasoningEngine with a scheduler agent:

- **Successful Scheduling**: Workflow with no conflicts
- **Conflict Detection**: Finding and handling scheduling conflicts
- **Alternative Suggestions**: Recommending different times
- **Silent Mode**: Running without reasoning output

**Run it:**
```bash
python examples/scheduler_reasoning_demo.py
```

## What You'll See

Both demos produce console output showing:
- Real-time thinking as the agent processes requests
- Categorized thoughts (ANALYSIS, PLANNING, DECISION, CONCERN, etc.)
- Reasoning summaries with thought counts by type
- JSON exports of reasoning chains

These examples are perfect for understanding how observable reasoning works before integrating it into your own agent!
