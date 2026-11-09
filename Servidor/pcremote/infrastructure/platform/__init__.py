"""Per-operating-system adapters selected by a factory."""

from __future__ import annotations

import importlib
import platform as _platform

from pcremote.domain.errors import UnsupportedActionError
from pcremote.infrastructure.platform.base import PlatformAdapters

__all__ = ["PlatformAdapters", "create_platform_adapters"]

_MODULES = {
    "Windows": "pcremote.infrastructure.platform.windows",
    "Darwin": "pcremote.infrastructure.platform.macos",
    "Linux": "pcremote.infrastructure.platform.linux",
}


def create_platform_adapters(app_name: str, startup_command: str, system: str | None = None) -> PlatformAdapters:
    """Build the adapters for `system` (defaults to the current operating system)."""
    name = system or _platform.system()
    module_name = _MODULES.get(name)
    if module_name is None:
        raise UnsupportedActionError("Unsupported platform")
    module = importlib.import_module(module_name)
    return module.build(app_name, startup_command)
