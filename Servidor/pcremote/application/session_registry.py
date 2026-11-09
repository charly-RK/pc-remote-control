"""Thread-safe registry of connected client sessions."""

from __future__ import annotations

import threading

from pcremote.domain.session import ClientSession


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, ClientSession] = {}
        self._lock = threading.Lock()

    def add(self, session: ClientSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session

    def get(self, session_id: str) -> ClientSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def remove(self, session_id: str) -> ClientSession | None:
        with self._lock:
            return self._sessions.pop(session_id, None)

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def authenticated(self) -> list[ClientSession]:
        with self._lock:
            return [s for s in self._sessions.values() if s.authenticated]

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def authenticated_count(self) -> int:
        return len(self.authenticated())
