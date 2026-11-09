"""Client session entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ClientSession:
    """A connected client. Authentication is tracked per connection."""

    session_id: str
    ip: str
    connected_at: datetime = field(default_factory=datetime.now)
    authenticated: bool = False
    device_name: str | None = None
    device_id: str | None = None
