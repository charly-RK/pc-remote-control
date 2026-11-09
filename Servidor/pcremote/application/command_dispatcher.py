"""Command dispatcher (Command + Registry pattern)."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from pcremote.domain.commands import CommandResult
from pcremote.domain.errors import InvalidPayloadError, NotAuthenticatedError, UnknownCommandError
from pcremote.domain.session import ClientSession

CommandHandler = Callable[[Mapping[str, Any]], CommandResult]


class CommandDispatcher:
    """Maps wire-level action names to handlers.

    Handlers are registered under one or more action names (aliases kept for
    clients that still send legacy names). Unknown actions are rejected.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, actions: Iterable[str] | str, handler: CommandHandler) -> None:
        names = (actions,) if isinstance(actions, str) else tuple(actions)
        for name in names:
            self._handlers[name] = handler

    def dispatch(self, session: ClientSession, payload: Mapping[str, Any]) -> CommandResult:
        if not session.authenticated:
            raise NotAuthenticatedError()
        if not isinstance(payload, Mapping):
            raise InvalidPayloadError("Command payload must be an object")
        action = payload.get("action")
        handler = self._handlers.get(action) if isinstance(action, str) else None
        if handler is None:
            raise UnknownCommandError(f"Unknown command: {action!r}")
        return handler(payload)
