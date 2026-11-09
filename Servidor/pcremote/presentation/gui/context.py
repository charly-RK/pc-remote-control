"""Dependencies handed to the GUI by the composition root."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pcremote.application.auth_service import AuthService
from pcremote.application.device_service import DeviceService
from pcremote.application.event_bus import EventBus
from pcremote.application.server_controller import ServerController
from pcremote.application.settings_service import SettingsService
from pcremote.domain.ports import AutoStartManager, FirewallManager


@dataclass
class GuiContext:
    server: ServerController
    auth: AuthService
    events: EventBus
    autostart: AutoStartManager
    settings: SettingsService
    devices: DeviceService
    firewall: FirewallManager
    assets_dir: Path
    on_exit: Callable[[], None]
    app_version: str = "1.0.0"
    platform_name: str = "Windows"  # platform.system() value, provided by the composition root
