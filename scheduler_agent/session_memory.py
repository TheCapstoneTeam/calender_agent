from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Optional, Callable, Any, List, Dict

from google.adk.memory import BaseMemoryService
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types


DEFAULT_SESSION_DB_NAME = "calendar_agent_sessions.db"
DEFAULT_MEMORY_DB_NAME = "calendar_agent_memory.db"


@dataclass
class SessionMemoryConfig:
    app_name: str
    user_id: str = "default"
    default_session_id: str = "default"
    session_db_name: str = DEFAULT_SESSION_DB_NAME
    memory_db_name: str = DEFAULT_MEMORY_DB_NAME
    storage_dir: Optional[Path | str] = None

    def storage_path(self) -> Path:
        base_dir = (
            Path(self.storage_dir)
            if self.storage_dir
            else Path(__file__).resolve().parent.parent / "data"
        )
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def session_db_url(self) -> str:
        db_file = self.storage_path() / self.session_db_name
        return f"sqlite+aiosqlite:///{db_file.as_posix()}"

    def memory_db_path(self) -> Path:
        return self.storage_path() / self.memory_db_name


class SQLiteMemoryService(BaseMemoryService):
    """
    A persistent memory service backed by SQLite.
    Stores session summaries and structured memories.
    """

    def __init__(self, db_path: Path):
        super().__init__()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Simple full-text search support
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, content='memories')
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                  INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
                END;
                """
            )

    async def add_session_to_memory(self, session: Any) -> None:
        """
        Persist relevant parts of the session to memory.
        For this simple implementation, we'll extract the last turn or summary.
        """
        # In a real implementation, we might use an LLM to summarize the session
        # or extract key facts. Here we just store the raw text of the last few turns.
        if not hasattr(session, "events"):
            return

        events = list(session.events)
        if not events:
            return

        # Simple extraction: Store the last user-model exchange as a memory unit
        # This is a naive implementation for demonstration.
        content_parts = []
        for event in events[-2:]: # Last 2 events
            text = self._extract_text(event)
            if text:
                role = getattr(event, "author", "unknown")
                content_parts.append(f"{role}: {text}")
        
        if not content_parts:
            return

        memory_content = "\n".join(content_parts)
        
        # Metadata
        metadata = {
            "session_id": getattr(session, "id", "unknown"),
            "event_count": len(events)
        }

        self._insert_memory(
            app_name="calendar_agent", # Should ideally come from config/context
            user_id="default", # Should come from context
            session_id=getattr(session, "id", "unknown"),
            content=memory_content,
            metadata=metadata
        )

    def _insert_memory(self, app_name: str, user_id: str, session_id: str, content: str, metadata: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memories (app_name, user_id, session_id, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (app_name, user_id, session_id, content, json.dumps(metadata))
            )

    async def search_memory(self, app_name: str, user_id: str, query: str, limit: int = 5) -> Any:
        """Search memories using FTS."""
        # Return a structure compatible with what the agent expects (e.g. list of objects with 'text' attribute)
        # The base class or agent might expect a specific return type. 
        # For now, returning a simple object wrapper.
        
        # Sanitize query for FTS5 (remove special characters that might break syntax)
        # We keep alphanumeric and spaces.
        import re
        safe_query = re.sub(r'[^a-zA-Z0-9\s]', '', query)
        
        # If query becomes empty after sanitization, return empty results
        if not safe_query.strip():
             return type('MemoryResponse', (), {'memories': []})

        results = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use the sanitized query
                cursor = conn.execute(
                    """
                    SELECT content, metadata, created_at FROM memories 
                    WHERE id IN (SELECT rowid FROM memories_fts WHERE memories_fts MATCH ? ORDER BY rank)
                    LIMIT ?
                    """,
                    (safe_query, limit)
                )
                for row in cursor:
                    # Construct a mock object that mimics the expected structure
                    # memory.content.parts[0].text
                    # memory.timestamp
                    
                    part = type('Part', (), {'text': row[0]})
                    content = type('Content', (), {'parts': [part]})
                    
                    results.append(type('MemoryResult', (), {
                        'text': row[0], 
                        'metadata': json.loads(row[1]), 
                        'created_at': row[2],
                        'timestamp': row[2],
                        'content': content,
                        'author': None # Add author alias for preload_memory_tool
                    }))
        except Exception as e:
            print(f"DEBUG: Error in search_memory: {e}")
            # Return empty list on error to prevent crash
            return type('MemoryResponse', (), {'memories': []})
        
        return type('MemoryResponse', (), {'memories': results})

    def _extract_text(self, event: Any) -> Optional[str]:
        # Helper to extract text from event object
        content = getattr(event, "content", None)
        if not content or not getattr(content, "parts", None):
            return None
        part = content.parts[0]
        return getattr(part, "text", None)


def build_persistent_session_service(config: SessionMemoryConfig) -> DatabaseSessionService:
    """Create or open the SQLite session store defined by the config."""
    try:
        url = config.session_db_url()
        print(f"DEBUG: Attempting to create DatabaseSessionService with URL: {url}")
        return DatabaseSessionService(db_url=url)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEBUG: Failed to create DatabaseSessionService: {e}")
        raise


def build_memory_service(config: SessionMemoryConfig) -> SQLiteMemoryService:
    """Return the persistent SQLite memory service."""
    return SQLiteMemoryService(db_path=config.memory_db_path())


async def auto_save_session_to_memory(callback_context: Any) -> None:
    """Callback that automatically persists the current session to memory."""
    invocation = getattr(callback_context, "_invocation_context", None)
    if invocation is None:
        return

    memory_service = getattr(invocation, "memory_service", None)
    session = getattr(invocation, "session", None)

    if not memory_service or not session:
        return

    try:
        await memory_service.add_session_to_memory(session)
    except Exception:
        # Even though we want persistence, memory failures should not stop the agent.
        pass


class SessionMemoryManager:
    """Utility helper that keeps session and memory workflows in one place."""

    def __init__(
        self,
        runner: Runner,
        session_service: DatabaseSessionService,
        memory_service: Optional[BaseMemoryService],
        config: SessionMemoryConfig,
    ) -> None:
        self.runner = runner
        self.session_service = session_service
        self.memory_service = memory_service
        self.config = config

    async def _get_session(self, session_id: Optional[str] = None):
        target_session = session_id or self.config.default_session_id
        try:
            return await self.session_service.create_session(
                app_name=self.config.app_name,
                user_id=self.config.user_id,
                session_id=target_session,
            )
        except Exception:
            return await self.session_service.get_session(
                app_name=self.config.app_name,
                user_id=self.config.user_id,
                session_id=target_session,
            )

    async def run_session(
        self,
        user_queries: Sequence[str] | str,
        session_id: Optional[str] = None,
        on_response: Optional[Callable[[str], Any]] = None,
        print_output: bool = True,
    ) -> List[str]:
        """Run a sequence of user queries inside a single session."""
        if not user_queries:
            return []

        session = await self._get_session(session_id)
        queries = [user_queries] if isinstance(user_queries, str) else list(user_queries)
        responses: List[str] = []

        for query in queries:
            if not query:
                continue

            query_content = types.Content(role="user", parts=[types.Part(text=query)])

            async for event in self.runner.run_async(
                user_id=self.config.user_id,
                session_id=session.id,
                new_message=query_content,
            ):
                text = self._extract_text(event)
                if not text:
                    continue

                responses.append(text)
                if on_response:
                    on_response(text)

                if print_output:
                    author = getattr(event, "author", None) or getattr(event.content, "role", "model")
                    print(f"{author} > {text}")

        await self._persist_session_to_memory(session)
        return responses

    async def _persist_session_to_memory(self, session: Any) -> None:
        if not self.memory_service:
            return
        try:
            await self.memory_service.add_session_to_memory(session)
        except Exception:
            pass

    @staticmethod
    def _extract_text(event: Any) -> Optional[str]:
        content = getattr(event, "content", None)
        if not content or not getattr(content, "parts", None):
            return None
        part = content.parts[0]
        return getattr(part, "text", None)

    async def search_memory(self, query: str, limit: int = 5) -> List[Any]:
        """Return raw memory entries that match the query."""
        if not self.memory_service:
            return []

        if not hasattr(self.memory_service, "search_memory"):
            return []

        response = await self.memory_service.search_memory(
            app_name=self.config.app_name,
            user_id=self.config.user_id,
            query=query,
            limit=limit,
        )
        return getattr(response, "memories", [])

    async def get_session_events(self, session_id: Optional[str] = None) -> List[Any]:
        """Retrieve raw events for a given session."""
        session = await self._get_session(session_id)
        return list(getattr(session, "events", []))


__all__ = [
    "SessionMemoryConfig",
    "build_persistent_session_service",
    "build_memory_service",
    "auto_save_session_to_memory",
    "SessionMemoryManager",
    "SQLiteMemoryService",
]
