"""Start-with-Windows support through the HKCU Run registry key."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from pcremote.domain.errors import ExecutionError

logger = logging.getLogger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def build_startup_command(background: bool = True) -> str:
    """Return the quoted command that launches the app at login."""
    suffix = " --background" if background else ""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"{suffix}'
    entry = Path(__file__).resolve().parents[3] / "main.py"
    python_exe = Path(sys.executable)
    windowless = python_exe.with_name("pythonw.exe")
    if windowless.exists():
        python_exe = windowless
    return f'"{python_exe}" "{entry}"{suffix}'


class WindowsAutoStart:
    def __init__(self, value_name: str, command: str) -> None:
        self._value_name = value_name
        self._command = command

    def is_enabled(self) -> bool:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, self._value_name)
            return True
        except FileNotFoundError:
            return False
        except OSError:
            logger.warning("Could not read the startup registry key", exc_info=True)
            return False

    def set_enabled(self, enabled: bool) -> None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
                if enabled:
                    winreg.SetValueEx(key, self._value_name, 0, winreg.REG_SZ, self._command)
                else:
                    try:
                        winreg.DeleteValue(key, self._value_name)
                    except FileNotFoundError:
                        pass
        except OSError as exc:
            raise ExecutionError(f"Could not update startup registry: {exc}") from exc
