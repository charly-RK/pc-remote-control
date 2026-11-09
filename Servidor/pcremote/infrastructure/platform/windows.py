"""Windows adapter set."""

from __future__ import annotations

from pcremote.infrastructure.platform.base import PlatformAdapters


def build(app_name: str, startup_command: str) -> PlatformAdapters:
    # Imports are local so that this module can be imported on any operating system.
    from pcremote.infrastructure.audio.pycaw_media import PycawMedia
    from pcremote.infrastructure.os.startup_registry import WindowsAutoStart
    from pcremote.infrastructure.os.window_watcher import WindowWatcher
    from pcremote.infrastructure.os.windows_firewall import WindowsFirewall
    from pcremote.infrastructure.power.windows_power import WindowsDesktop, WindowsPower

    return PlatformAdapters(
        power=WindowsPower(),
        desktop=WindowsDesktop(),
        media=PycawMedia(),
        autostart=WindowsAutoStart(app_name, startup_command),
        firewall=WindowsFirewall(),
        monitor_factory=WindowWatcher,
    )
