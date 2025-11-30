from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Optional, Callable, Any, List

from google.adk.memory import InMemoryMemoryService, MemoryService
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types



DEFAULT_SESSION_DB_NAME = "calendar_agent_sessions.db"


@dataclass
class SessionMemoryConfig:
    app_name: str
    user_id: str = "default"
    default_session_id: str = "default"
    session_db_name: str = DEFAULT_SESSION_DB_NAME
    storage_dir: Optional[Path | str] = None

    def storage_path(self) -> Path:
        base_dir = (
            Path(self.storage_dir)
            if self.storage_dir
            else Path(__file__).resolve().parent.parent / "data"
        )
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def database_url(self) -> str:
        db_file = self.storage_path() / self.session_db_name
        return f"sqlite:///{db_file.as_posix()}"


def build_persistent_session_service(config: SessionMemoryConfig) -> DatabaseSessionService:
    """Create or open the SQLite session store defined by the config."""
    return DatabaseSessionService(db_url=config.database_url())


def build_memory_service() -> InMemoryMemoryService:
    """Return the default in-memory memory service for prototyping."""
    return InMemoryMemoryService()


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
        memory_service: Optional[MemoryService],
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
]
