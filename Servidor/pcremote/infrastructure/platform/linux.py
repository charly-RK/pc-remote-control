"""Linux adapter set. Not validated on a real Linux desktop."""

from __future__ import annotations

import getpass
import logging
import os
import re
import shutil
import subprocess
import webbrowser
from pathlib import Path

from pcremote.domain.commands import DesktopAction, MediaCommand, MediaState, PowerAction
from pcremote.domain.errors import ExecutionError, UnsupportedActionError
from pcremote.domain.ports import EventPublisher
from pcremote.infrastructure.os._command import run_command, run_command_output, spawn_detached
from pcremote.infrastructure.os._polling_watcher import PollingWatcher
from pcremote.infrastructure.os.noop_firewall import NoopFirewall
from pcremote.infrastructure.platform.base import PlatformAdapters

logger = logging.getLogger(__name__)

_SINK = "@DEFAULT_SINK@"
_PERCENT = re.compile(r"(\d+)%")


def parse_pactl_volume(text: str) -> float | None:
    """First percentage of `pactl get-sink-volume`: Volume: front-left: 32768 / 50% / -18.06 dB."""
    match = _PERCENT.search(text)
    return min(int(match.group(1)), 100) / 100 if match else None


def parse_pactl_mute(text: str) -> bool | None:
    value = text.split(":", 1)[-1].strip().lower()
    return {"yes": True, "no": False}.get(value)


def parse_amixer(text: str) -> tuple[float | None, bool | None]:
    """`amixer sget Master`: ... Playback 42000 [64%] [on]."""
    volume = parse_pactl_volume(text)
    muted = None
    if "[off]" in text:
        muted = True
    elif "[on]" in text:
        muted = False
    return volume, muted
_PLAYER_ACTIONS: dict[MediaCommand, str] = {
    MediaCommand.PLAY_PAUSE: "play-pause",
    MediaCommand.NEXT: "next",
    MediaCommand.PREVIOUS: "previous",
}
_TASK_MANAGERS = ("gnome-system-monitor", "plasma-systemmonitor", "ksysguard")


class LinuxPower:
    def execute(self, action: PowerAction) -> None:
        logger.info("Executing power action: %s", action.value)
        commands: dict[PowerAction, list[str]] = {
            PowerAction.SHUTDOWN: ["systemctl", "poweroff"],
            PowerAction.RESTART: ["systemctl", "reboot"],
            PowerAction.SLEEP: ["systemctl", "suspend"],
            PowerAction.LOGOUT: ["loginctl", "terminate-user", getpass.getuser()],
            PowerAction.LOCK: ["loginctl", "lock-session"],
        }
        run_command(commands[action])


class LinuxDesktop:
    def execute(self, action: DesktopAction) -> None:
        if action is DesktopAction.OPEN_BROWSER:
            try:
                webbrowser.open("https://www.google.com")
            except webbrowser.Error as exc:
                raise ExecutionError("Could not open the browser") from exc
        elif action is DesktopAction.EXPLORER:
            run_command(["xdg-open", str(Path.home())])
        elif action is DesktopAction.TASK_MANAGER:
            self._open_task_manager()
        elif action is DesktopAction.CAPTURE:
            self._capture()
        elif action is DesktopAction.SHOW_DESKTOP:
            self._show_desktop()

    @staticmethod
    def _open_task_manager() -> None:
        for program in _TASK_MANAGERS:
            if shutil.which(program):
                spawn_detached([program])
                return
        raise UnsupportedActionError("No system monitor application was found")

    @staticmethod
    def _capture() -> None:
        if shutil.which("gnome-screenshot"):
            run_command(["gnome-screenshot", "-c"])
        elif shutil.which("spectacle"):
            run_command(["spectacle", "-b", "-c"])
        elif shutil.which("import"):
            target = Path.home() / "Pictures" / "screenshot.png"
            run_command(["import", "-window", "root", str(target)])
        else:
            raise UnsupportedActionError("No screenshot tool was found")

    @staticmethod
    def _show_desktop() -> None:
        import pyautogui

        try:
            pyautogui.hotkey("win", "d")
        except pyautogui.PyAutoGUIException as exc:
            raise ExecutionError("Could not send the key combination") from exc


class LinuxMedia:
    def send(self, command: MediaCommand) -> None:
        if command in _PLAYER_ACTIONS:
            self._require("playerctl")
            run_command(["playerctl", _PLAYER_ACTIONS[command]])
        elif command is MediaCommand.VOLUME_UP:
            self._change_volume("+5%", "5%+")
        elif command is MediaCommand.VOLUME_DOWN:
            self._change_volume("-5%", "5%-")
        elif command is MediaCommand.MUTE:
            if shutil.which("pactl"):
                run_command(["pactl", "set-sink-mute", _SINK, "toggle"])
            else:
                self._require("amixer")
                run_command(["amixer", "-D", "pulse", "sset", "Master", "toggle"])
        else:
            raise UnsupportedActionError(f"'{command.value}' is not supported on Linux")

    def set_volume(self, level: float) -> None:
        percent = round(level * 100)
        if shutil.which("pactl"):
            run_command(["pactl", "set-sink-volume", _SINK, f"{percent}%"])
        else:
            self._require("amixer")
            run_command(["amixer", "-D", "pulse", "sset", "Master", f"{percent}%"])

    def get_state(self) -> MediaState:
        """`playing` is not available without querying a specific player."""
        try:
            if shutil.which("pactl"):
                volume = parse_pactl_volume(run_command_output(["pactl", "get-sink-volume", _SINK]))
                muted = parse_pactl_mute(run_command_output(["pactl", "get-sink-mute", _SINK]))
            elif shutil.which("amixer"):
                volume, muted = parse_amixer(run_command_output(["amixer", "-D", "pulse", "sget", "Master"]))
            else:
                return MediaState()
        except ExecutionError:
            return MediaState()
        return MediaState(volume=volume, muted=muted, playing=None)

    def _change_volume(self, pactl_delta: str, amixer_delta: str) -> None:
        if shutil.which("pactl"):
            run_command(["pactl", "set-sink-volume", _SINK, pactl_delta])
        else:
            self._require("amixer")
            run_command(["amixer", "-D", "pulse", "sset", "Master", amixer_delta])

    @staticmethod
    def _require(program: str) -> None:
        if not shutil.which(program):
            raise UnsupportedActionError(f"'{program}' is required for this action")


class LinuxAutoStart:
    """XDG autostart entry (~/.config/autostart)."""

    def __init__(self, app_name: str, startup_command: str, autostart_dir: Path | None = None) -> None:
        self._app_name = app_name
        self._command = startup_command
        self._dir = autostart_dir or Path.home() / ".config" / "autostart"

    @property
    def desktop_path(self) -> Path:
        return self._dir / f"{self._app_name}.desktop"

    def render(self) -> str:
        return (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={self._app_name}\n"
            f"Exec={self._command}\n"
            "X-GNOME-Autostart-enabled=true\n"
            "Terminal=false\n"
        )

    def is_enabled(self) -> bool:
        return self.desktop_path.exists()

    def set_enabled(self, enabled: bool) -> None:
        try:
            if enabled:
                self._dir.mkdir(parents=True, exist_ok=True)
                self.desktop_path.write_text(self.render(), encoding="utf-8")
            else:
                self.desktop_path.unlink(missing_ok=True)
        except OSError as exc:
            raise ExecutionError(f"Could not update the autostart entry: {exc}") from exc


class LinuxWindowWatcher(PollingWatcher):
    """Uses xdotool; works on X11 sessions only."""

    def __init__(self, publisher: EventPublisher, interval: float = 1.0) -> None:
        super().__init__(publisher, self._read_active_window, interval, name="linux-window-watcher")

    def is_supported(self) -> bool:
        if shutil.which("xdotool") is None:
            logger.warning("xdotool not found; window watcher disabled")
            return False
        if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
            logger.warning("Wayland session without X11; window watcher disabled")
            return False
        return True

    @staticmethod
    def _read_active_window() -> str | None:
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            shell=False, check=False, capture_output=True, text=True, timeout=5,
        )
        title = result.stdout.strip()
        return title if result.returncode == 0 and title else None


def build(app_name: str, startup_command: str) -> PlatformAdapters:
    return PlatformAdapters(
        power=LinuxPower(),
        desktop=LinuxDesktop(),
        media=LinuxMedia(),
        autostart=LinuxAutoStart(app_name, startup_command),
        firewall=NoopFirewall(),
        monitor_factory=LinuxWindowWatcher,
    )
