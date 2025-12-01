import asyncio
import sys
import time
from scheduler_agent.agent import session_memory_manager

# ANSI colors for better visualization
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

async def type_text(text, delay=0.05):
    """Simulates typing effect."""
    sys.stdout.write(f"{BOLD}{BLUE}[user]: {RESET}")
    sys.stdout.flush()
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()  # Newline after typing
    time.sleep(0.5)  # Short pause after typing

class Tee:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.terminal.flush()
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

async def run_demo():
    # Redirect stdout to both terminal and file
    sys.stdout = Tee("adk_session.typescript")
    
    print(f"{GREEN}Starting Calendar Agent Demo...{RESET}\n")
    
    # Define the conversation flow based on the transcript
    conversation = [
        "schedule a meeting titled 'final' with [ellacharmed@gmail.com, kkella1211@gmail.com] on Dec 1st from 9am for 30min on our TeamElla calendar in Room B",
        "what do you know?",
        "how many events have you created?",
        "Schedule meeting with attendees ellacharmed@gmail.com, ruqaiya.sattar345@gmail.com, abdullahzunorain2@gmail.com, pro1943.235@gmail.com for Dec 2 3am for 5 min called 'capstone submission final hour'",
        "can you edit events?",
        "what do yo know now?",
        "what can you do other than create events?",
        "bye"
    ]

    session_id = f"demo-session-{int(time.time())}"

    for user_input in conversation:
        # 1. Simulate User Typing
        await type_text(user_input)

        # 2. Run Agent
        # We use print_output=True so the agent prints its own responses as they stream/arrive
        await session_memory_manager.run_session(
            user_queries=[user_input],
            session_id=session_id,
            print_output=True
        )
        
        # Add a pause between turns for the viewer to read
        print("\n" + "-"*40 + "\n")
        time.sleep(2)

import argparse

async def replay_demo(session_id):
    print(f"{GREEN}Replaying Session: {session_id}{RESET}\n")
    
    # Redirect stdout to both terminal and file
    sys.stdout = Tee("adk_session.typescript")

    events = await session_memory_manager.get_session_events(session_id)
    
    if not events:
        print(f"{BLUE}No events found for session: {session_id}{RESET}")
        return

    for event in events:
        # Extract text using the helper
        text = session_memory_manager._extract_text(event)
        if not text:
            continue
            
        # Determine role
        role = getattr(event, "author", None) or getattr(event.content, "role", "model")
        
        if role == "user":
            await type_text(text)
            print("\n" + "-"*40 + "\n")
            time.sleep(1)
        else:
            # Model/Agent output
            print(f"{role} > {text}")
            print("\n" + "-"*40 + "\n")
            time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Calendar Agent Demo")
    parser.add_argument("--replay", type=str, help="Session ID to replay")
    args = parser.parse_args()

    try:
        if args.replay:
            asyncio.run(replay_demo(args.replay))
        else:
            asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nDemo stopped by user.")
