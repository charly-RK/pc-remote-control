import plistlib
import subprocess

import pytest

from pcremote.domain.commands import DesktopAction, MediaCommand, PowerAction
from pcremote.domain.errors import ExecutionError, UnsupportedActionError
from pcremote.domain.events import ActiveWindowChanged
from pcremote.infrastructure.os import windows_firewall
from pcremote.infrastructure.os._polling_watcher import PollingWatcher
from pcremote.infrastructure.os.noop_firewall import NoopFirewall
from pcremote.infrastructure.platform import create_platform_adapters
from pcremote.infrastructure.platform.linux import LinuxAutoStart, LinuxDesktop, LinuxMedia, LinuxPower
from pcremote.infrastructure.platform.macos import MacAutoStart, MacDesktop, MacMedia, MacPower

from .fakes import RecordingPublisher


class CommandRecorder:
    """Replaces subprocess.run / Popen and records the argument lists."""

    def __init__(self, monkeypatch, returncode=0, available=None):
        self.calls: list[list[str]] = []
        self.spawned: list[list[str]] = []
        self.returncode = returncode
        monkeypatch.setattr(subprocess, "run", self._run)
        monkeypatch.setattr(subprocess, "Popen", lambda args, **kw: self.spawned.append(list(args)))
        if available is not None:
            monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name in available else None)

    def _run(self, args, **kwargs):
        assert kwargs.get("shell") is False
        self.calls.append(list(args))
        return subprocess.CompletedProcess(args, self.returncode, stdout=b"", stderr=b"")


def test_factory_selects_adapters_by_system():
    for system, power_name in (("Darwin", "MacPower"), ("Linux", "LinuxPower")):
        adapters = create_platform_adapters("PCRemoteControl", "/opt/app --background", system=system)
        assert type(adapters.power).__name__ == power_name
        assert adapters.firewall.is_configured() is True
    windows = create_platform_adapters("PCRemoteControl", '"C:\\app.exe" --background', system="Windows")
    assert type(windows.firewall).__name__ == "WindowsFirewall"


def test_factory_rejects_unknown_system():
    with pytest.raises(UnsupportedActionError):
        create_platform_adapters("x", "y", system="Plan9")


def test_mac_power_and_desktop_commands(monkeypatch):
    rec = CommandRecorder(monkeypatch)
    MacPower().execute(PowerAction.SLEEP)
    MacPower().execute(PowerAction.SHUTDOWN)
    MacDesktop().execute(DesktopAction.CAPTURE)
    MacDesktop().execute(DesktopAction.TASK_MANAGER)
    assert rec.calls[0] == ["pmset", "sleepnow"]
    assert rec.calls[1][:2] == ["osascript", "-e"] and "shut down" in rec.calls[1][2]
    assert rec.calls[2] == ["screencapture", "-c"]
    assert rec.calls[3] == ["open", "-a", "Activity Monitor"]


def test_mac_media_volume_and_unsupported(monkeypatch):
    rec = CommandRecorder(monkeypatch)
    MacMedia().set_volume(0.5)
    assert rec.calls[-1] == ["osascript", "-e", "set volume output volume 50"]
    with pytest.raises(UnsupportedActionError):
        MacMedia().send(MediaCommand.GAME_BAR)


def test_mac_media_player_control_needs_running_player(monkeypatch):
    rec = CommandRecorder(monkeypatch, returncode=1)  # pgrep finds nothing
    with pytest.raises(UnsupportedActionError):
        MacMedia().send(MediaCommand.PLAY_PAUSE)
    rec.returncode = 0
    MacMedia().send(MediaCommand.NEXT)
    assert rec.calls[-1][2] == 'tell application "Spotify" to next track'


def test_linux_power_and_media_commands(monkeypatch):
    rec = CommandRecorder(monkeypatch, available={"pactl", "playerctl"})
    LinuxPower().execute(PowerAction.SHUTDOWN)
    LinuxPower().execute(PowerAction.LOCK)
    LinuxMedia().send(MediaCommand.PLAY_PAUSE)
    LinuxMedia().send(MediaCommand.VOLUME_UP)
    LinuxMedia().set_volume(0.3)
    assert rec.calls == [
        ["systemctl", "poweroff"],
        ["loginctl", "lock-session"],
        ["playerctl", "play-pause"],
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "30%"],
    ]


def test_linux_volume_falls_back_to_amixer(monkeypatch):
    rec = CommandRecorder(monkeypatch, available={"amixer"})
    LinuxMedia().send(MediaCommand.VOLUME_DOWN)
    assert rec.calls == [["amixer", "-D", "pulse", "sset", "Master", "5%-"]]


def test_linux_missing_tools_are_reported(monkeypatch):
    CommandRecorder(monkeypatch, available=set())
    with pytest.raises(UnsupportedActionError):
        LinuxMedia().send(MediaCommand.PLAY_PAUSE)
    with pytest.raises(UnsupportedActionError):
        LinuxDesktop().execute(DesktopAction.TASK_MANAGER)
    with pytest.raises(UnsupportedActionError):
        LinuxMedia().send(MediaCommand.RECORD)


def test_linux_task_manager_and_capture(monkeypatch):
    rec = CommandRecorder(monkeypatch, available={"gnome-system-monitor", "gnome-screenshot"})
    LinuxDesktop().execute(DesktopAction.TASK_MANAGER)
    LinuxDesktop().execute(DesktopAction.CAPTURE)
    assert rec.spawned == [["gnome-system-monitor"]]
    assert rec.calls == [["gnome-screenshot", "-c"]]


def test_command_failure_becomes_execution_error(monkeypatch):
    def boom(args, **kwargs):
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(subprocess, "run", boom)
    with pytest.raises(ExecutionError):
        LinuxPower().execute(PowerAction.RESTART)


def test_mac_launch_agent_roundtrip(tmp_path):
    autostart = MacAutoStart("PCRemoteControl", '"/Applications/PC Remote.app/run" --background', agents_dir=tmp_path)
    assert not autostart.is_enabled()
    autostart.set_enabled(True)
    data = plistlib.loads(autostart.plist_path.read_bytes())
    assert data["Label"] == "com.riskkeep.PCRemoteControl"
    assert data["ProgramArguments"] == ["/Applications/PC Remote.app/run", "--background"]
    assert data["RunAtLoad"] is True and autostart.is_enabled()
    autostart.set_enabled(False)
    assert not autostart.is_enabled()


def test_linux_autostart_desktop_file(tmp_path):
    autostart = LinuxAutoStart(
        "PCRemoteControl", "/opt/pcremote/run --background", autostart_dir=tmp_path / "autostart"
    )
    autostart.set_enabled(True)
    text = autostart.desktop_path.read_text(encoding="utf-8")
    assert "[Desktop Entry]" in text and "Exec=/opt/pcremote/run --background" in text
    assert autostart.is_enabled()
    autostart.set_enabled(False)
    assert not autostart.is_enabled()


def test_windows_firewall_rule_arguments(monkeypatch):
    monkeypatch.setattr(windows_firewall, "program_path", lambda: "C:\\Apps\\PCRemoteControl.exe")
    args = windows_firewall.WindowsFirewall().add_rule_args()
    assert args[:2] == ["add", "rule"]
    for expected in ("name=PC Remote Control", "dir=in", "action=allow", "protocol=any",
                     "profile=private,domain", "program=C:\\Apps\\PCRemoteControl.exe"):
        assert expected in args


def test_windows_firewall_configure_as_admin_runs_netsh(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        is_show = "show" in args
        return subprocess.CompletedProcess(args, 1 if is_show else 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(windows_firewall, "is_admin", lambda: True)
    assert windows_firewall.WindowsFirewall().configure() is True
    assert calls[0][:4] == ["netsh", "advfirewall", "firewall", "show"]
    assert calls[1][:5] == ["netsh", "advfirewall", "firewall", "add", "rule"]


def test_windows_firewall_not_admin_requests_elevation(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: subprocess.CompletedProcess(args, 1))
    monkeypatch.setattr(windows_firewall, "is_admin", lambda: False)
    requested = []
    monkeypatch.setattr(
        windows_firewall.WindowsFirewall,
        "_relaunch_elevated",
        lambda self, flag, expect_configured: requested.append((flag, expect_configured)) or True,
    )
    assert windows_firewall.WindowsFirewall().configure() is True
    assert requested == [("--configure-firewall", True)]


def test_noop_firewall():
    firewall = NoopFirewall()
    assert firewall.is_configured() and firewall.configure() and firewall.remove()


def test_polling_watcher_publishes_only_on_change():
    bus = RecordingPublisher()
    titles = iter(["Notepad - a", "Notepad - a", "Terminal", None])
    watcher = PollingWatcher(bus, lambda: next(titles))
    for _ in range(4):
        watcher.poll_once()
    assert [(e.title, e.accepts_text) for e in bus.events if isinstance(e, ActiveWindowChanged)] == [
        ("Notepad - a", True),
        ("Terminal", False),
    ]
