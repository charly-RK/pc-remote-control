"""Platform adapter bundle (Abstract Factory product)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pcremote.domain.ports import (
    ActivityMonitor,
    AutoStartManager,
    DesktopController,
    EventPublisher,
    FirewallManager,
    MediaController,
    PowerController,
)


@dataclass(frozen=True)
class PlatformAdapters:
    power: PowerController
    desktop: DesktopController
    media: MediaController
    autostart: AutoStartManager
    firewall: FirewallManager
    monitor_factory: Callable[[EventPublisher], ActivityMonitor]
