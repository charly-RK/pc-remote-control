"""Ports: contracts that the application needs from the outside world.

Adapters in `pcremote.infrastructure` (and the transport in presentation)
implement these. Nothing here may import a framework or OS library.
"""

from __future__ import annotations

from typing import Protocol

from .commands import (
    ClickType,
    DesktopAction,
    KeyAction,
    MediaCommand,
    MediaState,
    MouseButton,
    PowerAction,
)
from .devices import PairedDevice
from .settings import AppSettings


class MouseController(Protocol):
    def move_relative(self, dx: int, dy: int) -> None: ...

    def click(self, button: MouseButton, click_type: ClickType) -> None: ...

    def scroll(self, dx: int, dy: int) -> None: ...


class KeyboardController(Protocol):
    def press_key(self, key: str, action: KeyAction) -> None: ...

    def hotkey(self, keys: list[str]) -> None: ...

    def type_text(self, text: str) -> None: ...


class MediaController(Protocol):
    def send(self, command: MediaCommand) -> None: ...

    def set_volume(self, level: float) -> None: ...

    def get_state(self) -> MediaState: ...


class PowerController(Protocol):
    def execute(self, action: PowerAction) -> None: ...


class DesktopController(Protocol):
    def execute(self, action: DesktopAction) -> None: ...


class PinStore(Protocol):
    def load(self) -> str | None: ...

    def save(self, pin: str) -> None: ...

    def clear(self) -> None: ...


class NetworkInspector(Protocol):
    def local_ip(self) -> str: ...

    def hostname(self) -> str: ...

    def is_port_free(self, port: int) -> bool: ...


class AutoStartManager(Protocol):
    def is_enabled(self) -> bool: ...

    def set_enabled(self, enabled: bool) -> None: ...


class TransportServer(Protocol):
    """The network server that accepts client connections."""

    def start(self, port: int) -> None: ...

    def stop(self) -> None: ...


class ActivityMonitor(Protocol):
    """Watches the desktop and publishes events (for example active window)."""

    def start(self) -> None: ...

    def stop(self) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event: object) -> None: ...


class DeviceRepository(Protocol):
    def list(self) -> list[PairedDevice]: ...

    def find_by_token_hash(self, token_hash: str) -> PairedDevice | None: ...

    def add(self, device: PairedDevice) -> None: ...

    def remove(self, device_id: str) -> bool: ...

    def touch(self, device_id: str, timestamp: float) -> None: ...


class SettingsStore(Protocol):
    def load(self) -> AppSettings: ...

    def save(self, settings: AppSettings) -> None: ...


class DiscoveryService(Protocol):
    """Announces the server on the local network (mDNS/Zeroconf)."""

    def start(self, server_id: str, name: str, ip: str, port: int, protocol_version: int) -> None: ...

    def stop(self) -> None: ...


class FirewallManager(Protocol):
    """Allows inbound connections for the application on private networks."""

    def is_configured(self) -> bool: ...

    def configure(self) -> bool:
        """Create the rule. May request elevation. Returns True when the rule exists afterwards."""
        ...

    def remove(self) -> bool: ...
