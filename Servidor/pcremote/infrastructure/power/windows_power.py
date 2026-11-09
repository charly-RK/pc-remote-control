"""Power and desktop adapters for Windows."""

from __future__ import annotations

import logging
import subprocess
import sys
import webbrowser

import pyautogui

from pcremote.domain.commands import DesktopAction, PowerAction
from pcremote.domain.errors import ExecutionError, UnsupportedActionError

logger = logging.getLogger(__name__)

_POWER_COMMANDS: dict[PowerAction, list[str]] = {
    PowerAction.SHUTDOWN: ["shutdown", "/s", "/t", "0"],
    PowerAction.RESTART: ["shutdown", "/r", "/t", "0"],
    PowerAction.SLEEP: ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
    PowerAction.LOGOUT: ["shutdown", "/l"],
    PowerAction.LOCK: ["rundll32.exe", "user32.dll,LockWorkStation"],
}

_DESKTOP_HOTKEYS: dict[DesktopAction, tuple[str, ...]] = {
    DesktopAction.TASK_MANAGER: ("ctrl", "shift", "esc"),
    DesktopAction.EXPLORER: ("win", "e"),
    DesktopAction.SHOW_DESKTOP: ("win", "d"),
}


def _require_windows() -> None:
    if sys.platform != "win32":
        raise UnsupportedActionError("This action is only supported on Windows")


class WindowsPower:
    def execute(self, action: PowerAction) -> None:
        _require_windows()
        logger.info("Executing power action: %s", action.value)
        try:
            subprocess.run(_POWER_COMMANDS[action], shell=False, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ExecutionError(f"Power action failed: {exc}") from exc


class WindowsDesktop:
    def execute(self, action: DesktopAction) -> None:
        _require_windows()
        try:
            if action in _DESKTOP_HOTKEYS:
                pyautogui.hotkey(*_DESKTOP_HOTKEYS[action])
            elif action is DesktopAction.CAPTURE:
                pyautogui.press("printscreen")
            elif action is DesktopAction.OPEN_BROWSER:
                webbrowser.open("https://www.google.com")
        except (pyautogui.PyAutoGUIException, webbrowser.Error) as exc:
            raise ExecutionError(f"Desktop action failed: {exc}") from exc
