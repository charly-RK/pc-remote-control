"""Windows firewall rule for the application (program-based, private and domain networks)."""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path

from pcremote.domain.errors import ExecutionError

logger = logging.getLogger(__name__)

RULE_NAME = "PC Remote Control"
_ELEVATION_WAIT_SECONDS = 15.0
_SHELL_EXECUTE_OK_THRESHOLD = 32


def is_admin() -> bool:
    if sys.platform != "win32":
        return False
    import ctypes

    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def program_path() -> str:
    """Executable the rule applies to: the frozen exe, or the Python interpreter in development."""
    if getattr(sys, "frozen", False):
        return sys.executable
    path = Path(sys.executable)
    if path.name.lower() == "pythonw.exe":
        path = path.with_name("python.exe")
    return str(path)


class WindowsFirewall:
    def __init__(self, rule_name: str = RULE_NAME) -> None:
        self._rule_name = rule_name

    def is_configured(self) -> bool:
        result = self._netsh(["show", "rule", f"name={self._rule_name}"])
        return result.returncode == 0

    def configure(self) -> bool:
        if self.is_configured():
            return True
        if not is_admin():
            return self._relaunch_elevated("--configure-firewall", expect_configured=True)
        result = self._netsh(self.add_rule_args())
        if result.returncode != 0:
            raise ExecutionError("Could not create the firewall rule")
        logger.info("Firewall rule created")
        return True

    def remove(self) -> bool:
        if not self.is_configured():
            return True
        if not is_admin():
            return self._relaunch_elevated("--remove-firewall", expect_configured=False)
        result = self._netsh(["delete", "rule", f"name={self._rule_name}"])
        return result.returncode == 0

    def add_rule_args(self) -> list[str]:
        return [
            "add", "rule",
            f"name={self._rule_name}",
            "dir=in",
            "action=allow",
            f"program={program_path()}",
            "enable=yes",
            "profile=private,domain",
            "protocol=any",
        ]

    @staticmethod
    def _netsh(args: list[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                ["netsh", "advfirewall", "firewall", *args],
                shell=False, check=False, capture_output=True, timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ExecutionError("netsh is not available") from exc

    def _relaunch_elevated(self, flag: str, expect_configured: bool) -> bool:
        """Re-run this program elevated (UAC prompt) with the given flag and wait for the result."""
        if sys.platform != "win32":
            raise ExecutionError("Firewall configuration is only supported on Windows")
        import ctypes

        if getattr(sys, "frozen", False):
            executable, params = sys.executable, flag
        else:
            main_script = Path(__file__).resolve().parents[3] / "main.py"
            executable, params = sys.executable, f'"{main_script}" {flag}'
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 0)
        if result <= _SHELL_EXECUTE_OK_THRESHOLD:
            logger.warning("Elevation was cancelled or failed")
            return False
        deadline = time.monotonic() + _ELEVATION_WAIT_SECONDS
        while time.monotonic() < deadline:
            if self.is_configured() == expect_configured:
                return True
            time.sleep(0.5)
        return self.is_configured() == expect_configured
