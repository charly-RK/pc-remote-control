"""macOS adapter set. Not validated on real macOS hardware."""

from __future__ import annotations

import logging
import plistlib
import shlex
import subprocess
import webbrowser
from pathlib import Path

from pcremote.domain.commands import DesktopAction, MediaCommand, MediaState, PowerAction
from pcremote.domain.errors import ExecutionError, UnsupportedActionError
from pcremote.domain.ports import EventPublisher
from pcremote.infrastructure.os._command import run_command, run_command_output
from pcremote.infrastructure.os._polling_watcher import PollingWatcher
from pcremote.infrastructure.os.noop_firewall import NoopFirewall
from pcremote.infrastructure.platform.base import PlatformAdapters

logger = logging.getLogger(__name__)

_FRONTMOST_SCRIPT = (
    'tell application "System Events" to get name of first application process whose frontmost is true'
)
_VOLUME_STEP = 6
_MEDIA_PLAYERS = ("Spotify", "Music")
_PLAYER_VERBS: dict[MediaCommand, str] = {
    MediaCommand.PLAY_PAUSE: "playpause",
    MediaCommand.NEXT: "next track",
    MediaCommand.PREVIOUS: "previous track",
}


def _osascript(script: str) -> None:
    run_command(["osascript", "-e", script])


def parse_mac_volume_settings(text: str) -> tuple[float | None, bool | None]:
    """Parse `get volume settings`: output volume:50, input volume:50, ..., output muted:false."""
    volume: float | None = None
    muted: bool | None = None
    for part in text.replace("\n", ",").split(","):
        key, _, value = part.partition(":")
        key, value = key.strip().lower(), value.strip().lower()
        if key == "output volume" and value.isdigit():
            volume = min(int(value), 100) / 100
        elif key == "output muted" and value in {"true", "false"}:
            muted = value == "true"
    return volume, muted


class MacPower:
    """Note: `lock` only turns the display off; the Mac locks if a password is required on wake."""

    def execute(self, action: PowerAction) -> None:
        logger.info("Executing power action: %s", action.value)
        commands: dict[PowerAction, list[str]] = {
            PowerAction.SHUTDOWN: ["osascript", "-e", 'tell app "System Events" to shut down'],
            PowerAction.RESTART: ["osascript", "-e", 'tell app "System Events" to restart'],
            PowerAction.SLEEP: ["pmset", "sleepnow"],
            PowerAction.LOGOUT: ["osascript", "-e", 'tell app "System Events" to log out'],
            PowerAction.LOCK: ["pmset", "displaysleepnow"],
        }
        run_command(commands[action])


class MacDesktop:
    def execute(self, action: DesktopAction) -> None:
        if action is DesktopAction.TASK_MANAGER:
            run_command(["open", "-a", "Activity Monitor"])
        elif action is DesktopAction.EXPLORER:
            run_command(["open", str(Path.home())])
        elif action is DesktopAction.CAPTURE:
            run_command(["screencapture", "-c"])
        elif action is DesktopAction.SHOW_DESKTOP:
            self._press_f11()
        elif action is DesktopAction.OPEN_BROWSER:
            try:
                webbrowser.open("https://www.google.com")
            except webbrowser.Error as exc:
                raise ExecutionError("Could not open the browser") from exc

    @staticmethod
    def _press_f11() -> None:
        import pyautogui

        try:
            pyautogui.press("f11")
        except pyautogui.PyAutoGUIException as exc:
            raise ExecutionError("Could not send the key press") from exc


class MacMedia:
    def send(self, command: MediaCommand) -> None:
        if command in _PLAYER_VERBS:
            self._control_player(_PLAYER_VERBS[command])
        elif command is MediaCommand.VOLUME_UP:
            _osascript(f"set volume output volume ((output volume of (get volume settings)) + {_VOLUME_STEP})")
        elif command is MediaCommand.VOLUME_DOWN:
            _osascript(f"set volume output volume ((output volume of (get volume settings)) - {_VOLUME_STEP})")
        elif command is MediaCommand.MUTE:
            _osascript("set volume output muted (not (output muted of (get volume settings)))")
        else:
            raise UnsupportedActionError(f"'{command.value}' is not supported on macOS")

    def set_volume(self, level: float) -> None:
        _osascript(f"set volume output volume {round(level * 100)}")

    def get_state(self) -> MediaState:
        """`playing` is not available on macOS without querying a specific player."""
        try:
            text = run_command_output(["osascript", "-e", "get volume settings"])
        except ExecutionError:
            return MediaState()
        volume, muted = parse_mac_volume_settings(text)
        return MediaState(volume=volume, muted=muted, playing=None)

    @staticmethod
    def _control_player(verb: str) -> None:
        for player in _MEDIA_PLAYERS:
            probe = subprocess.run(["pgrep", "-x", player], shell=False, check=False, capture_output=True, timeout=10)
            if probe.returncode == 0:
                _osascript(f'tell application "{player}" to {verb}')
                return
        raise UnsupportedActionError("No supported media player (Spotify or Music) is running")


class MacAutoStart:
    """Login item through a per-user LaunchAgent."""

    def __init__(self, app_name: str, startup_command: str, agents_dir: Path | None = None) -> None:
        self._label = f"com.riskkeep.{app_name}"
        self._command = startup_command
        self._agents_dir = agents_dir or Path.home() / "Library" / "LaunchAgents"

    @property
    def plist_path(self) -> Path:
        return self._agents_dir / f"{self._label}.plist"

    def is_enabled(self) -> bool:
        return self.plist_path.exists()

    def set_enabled(self, enabled: bool) -> None:
        try:
            if enabled:
                self._agents_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "Label": self._label,
                    "ProgramArguments": shlex.split(self._command),
                    "RunAtLoad": True,
                    "ProcessType": "Interactive",
                }
                with self.plist_path.open("wb") as handle:
                    plistlib.dump(payload, handle)
            else:
                self.plist_path.unlink(missing_ok=True)
        except OSError as exc:
            raise ExecutionError(f"Could not update the login item: {exc}") from exc


class MacWindowWatcher(PollingWatcher):
    def __init__(self, publisher: EventPublisher, interval: float = 1.0) -> None:
        super().__init__(publisher, self._read_frontmost, interval, name="mac-window-watcher")

    @staticmethod
    def _read_frontmost() -> str | None:
        result = subprocess.run(
            ["osascript", "-e", _FRONTMOST_SCRIPT],
            shell=False, check=False, capture_output=True, text=True, timeout=5,
        )
        title = result.stdout.strip()
        return title if result.returncode == 0 and title else None


def build(app_name: str, startup_command: str) -> PlatformAdapters:
    return PlatformAdapters(
        power=MacPower(),
        desktop=MacDesktop(),
        media=MacMedia(),
        autostart=MacAutoStart(app_name, startup_command),
        firewall=NoopFirewall(),
        monitor_factory=MacWindowWatcher,
    )
