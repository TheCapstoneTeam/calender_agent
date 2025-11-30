import pytest
import sqlite3
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import List, Any

from scheduler_agent.session_memory import SQLiteMemoryService

# Mock classes for Session and Event
@dataclass
class MockPart:
    text: str

@dataclass
class MockContent:
    parts: List[MockPart]
    role: str = "user"

@dataclass
class MockEvent:
    content: MockContent
    author: str = "user"

@dataclass
class MockSession:
    id: str
    events: List[MockEvent]
    app_name: str = "test_app"
    user_id: str = "test_user"

@pytest.fixture
def memory_db_path(tmp_path):
    """Fixture to provide a temporary database path."""
    return tmp_path / "test_memory.db"

@pytest.fixture
def memory_service(memory_db_path):
    """Fixture to provide an initialized SQLiteMemoryService."""
    return SQLiteMemoryService(db_path=memory_db_path)

@pytest.mark.asyncio
async def test_init_db(memory_db_path):
    """Test that the database and tables are created upon initialization."""
    service = SQLiteMemoryService(db_path=memory_db_path)
    
    assert memory_db_path.exists()
    
    with sqlite3.connect(memory_db_path) as conn:
        cursor = conn.cursor()
        
        # Check memories table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
        assert cursor.fetchone() is not None
        
        # Check FTS table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'")
        assert cursor.fetchone() is not None

@pytest.mark.asyncio
async def test_add_session_to_memory(memory_service, memory_db_path):
    """Test adding a session to memory."""
    # Create a mock session with some events
    events = [
        MockEvent(content=MockContent(parts=[MockPart(text="Hello")])),
        MockEvent(content=MockContent(parts=[MockPart(text="Hi there")], role="model"), author="model"),
        MockEvent(content=MockContent(parts=[MockPart(text="My favorite color is blue")])),
        MockEvent(content=MockContent(parts=[MockPart(text="Noted, blue.")], role="model"), author="model")
    ]
    session = MockSession(id="session_123", events=events)
    
    await memory_service.add_session_to_memory(session)
    
    # Verify data in DB
    with sqlite3.connect(memory_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content, metadata FROM memories")
        row = cursor.fetchone()
        
        assert row is not None
        content, metadata_json = row
        
        # Check content (should contain last 2 turns)
        assert "My favorite color is blue" in content
        assert "Noted, blue." in content
        
        # Check metadata
        metadata = json.loads(metadata_json)
        assert metadata["session_id"] == "session_123"
        assert metadata["event_count"] == 4

@pytest.mark.asyncio
async def test_search_memory(memory_service):
    """Test searching memory."""
    # Insert some test data directly or via add_session_to_memory
    # Let's use add_session_to_memory to test the full flow
    
    events1 = [
        MockEvent(content=MockContent(parts=[MockPart(text="I like pizza")]), author="user"),
        MockEvent(content=MockContent(parts=[MockPart(text="Pizza is great")]), author="model")
    ]
    session1 = MockSession(id="s1", events=events1)
    await memory_service.add_session_to_memory(session1)
    
    events2 = [
        MockEvent(content=MockContent(parts=[MockPart(text="I like sushi")]), author="user"),
        MockEvent(content=MockContent(parts=[MockPart(text="Sushi is awesome")]), author="model")
    ]
    session2 = MockSession(id="s2", events=events2)
    await memory_service.add_session_to_memory(session2)
    
    # Search for "pizza"
    result = await memory_service.search_memory("test_app", "test_user", "pizza")
    memories = result.memories
    
    assert len(memories) >= 1
    assert "pizza" in memories[0].text.lower()
    
    # Search for "sushi"
    result = await memory_service.search_memory("test_app", "test_user", "sushi")
    memories = result.memories
    
    assert len(memories) >= 1
    assert "sushi" in memories[0].text.lower()

@pytest.mark.asyncio
async def test_empty_session_ignored(memory_service, memory_db_path):
    """Test that empty sessions are not persisted."""
    session = MockSession(id="empty", events=[])
    await memory_service.add_session_to_memory(session)
    
    with sqlite3.connect(memory_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM memories")
        count = cursor.fetchone()[0]
        assert count == 0
