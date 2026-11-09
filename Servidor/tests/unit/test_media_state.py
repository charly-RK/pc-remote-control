from types import SimpleNamespace

import pytest

from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.application.handlers.media import MediaHandlers
from pcremote.domain.commands import CommandResult, MediaCommand, MediaRequest, MediaState
from pcremote.domain.errors import InvalidPayloadError
from pcremote.domain.session import ClientSession
from pcremote.infrastructure.audio.pycaw_media import any_active_session
from pcremote.infrastructure.platform.linux import parse_amixer, parse_pactl_mute, parse_pactl_volume
from pcremote.infrastructure.platform.macos import parse_mac_volume_settings

from .fakes import FakeMedia


@pytest.fixture
def session():
    s = ClientSession("sid", "10.0.0.2")
    s.authenticated = True
    return s


def make(media=None, sleeps=None):
    media = media or FakeMedia()
    sleeps = sleeps if sleeps is not None else []
    dispatcher = CommandDispatcher()
    MediaHandlers(media, settle_seconds=0.04, sleep=sleeps.append).register(dispatcher)
    return dispatcher, media, sleeps


# ------------------------------------------------------------------ domain


def test_get_state_command_parses():
    assert MediaRequest.parse({"command": "get_state"}).command is MediaCommand.GET_STATE
    with pytest.raises(InvalidPayloadError):
        MediaRequest.parse({"command": "get_states"})


def test_command_result_data_is_optional():
    assert CommandResult.success("x").data is None
    assert CommandResult.success("x", data={"a": 1}).data == {"a": 1}


def test_media_state_defaults_to_unknown():
    assert MediaState().to_dict() == {"volume": None, "muted": None, "playing": None}


# ------------------------------------------------------------------ handlers


@pytest.mark.parametrize("alias", ["media", "media_control"])
def test_get_state_works_with_both_aliases_and_sends_no_key(session, alias):
    dispatcher, media, sleeps = make()
    result = dispatcher.dispatch(session, {"action": alias, "command": "get_state"})
    assert result.ok and result.data == {"volume": 0.5, "muted": False, "playing": True}
    assert media.calls == [] and sleeps == []


@pytest.mark.parametrize("command", ["volume_up", "volume_down", "mute", "play_pause", "next", "previous"])
def test_key_commands_wait_then_return_state(session, command):
    dispatcher, media, sleeps = make()
    result = dispatcher.dispatch(session, {"action": "media_control", "command": command})
    assert result.data == {"volume": 0.5, "muted": False, "playing": True}
    assert media.calls == [("send", MediaCommand(command))]
    assert sleeps == [0.04]


def test_set_volume_returns_state_without_settle_delay(session):
    dispatcher, media, sleeps = make()
    result = dispatcher.dispatch(session, {"action": "media_control", "command": "set_volume", "level": 0.3})
    assert media.calls == [("volume", 0.3)]
    assert result.data is not None and sleeps == []


def test_state_read_failure_does_not_fail_the_command(session):
    media = FakeMedia()
    media.fail_state = True
    dispatcher, _, _ = make(media)
    result = dispatcher.dispatch(session, {"action": "media_control", "command": "mute"})
    assert result.ok is True
    assert result.data == {"volume": None, "muted": None, "playing": None}


# ------------------------------------------------------------------ adapter parsing


def test_mac_volume_settings_parsing():
    text = "output volume:42, input volume:50, alert volume:100, output muted:false"
    assert parse_mac_volume_settings(text) == (0.42, False)
    assert parse_mac_volume_settings("output volume:missing value, output muted:true") == (None, True)
    assert parse_mac_volume_settings("") == (None, None)


def test_linux_pactl_and_amixer_parsing():
    out = "Volume: front-left: 32768 /  50% / -18.06 dB,   front-right: 32768 /  50% / -18.06 dB"
    assert parse_pactl_volume(out) == 0.5
    assert parse_pactl_volume("nothing") is None
    assert parse_pactl_mute("Mute: yes") is True
    assert parse_pactl_mute("Mute: no") is False
    assert parse_pactl_mute("???") is None
    assert parse_amixer("Mono: Playback 42000 [64%] [on]") == (0.64, False)
    assert parse_amixer("Mono: Playback 0 [0%] [off]") == (0.0, True)


def _session(pid, process, state):
    return SimpleNamespace(ProcessId=pid, Process=process, State=state)


def test_windows_playing_heuristic_ignores_system_sounds_and_own_process():
    browser = _session(100, object(), 1)
    idle = _session(101, object(), 0)
    system_sounds = _session(0, None, 1)
    own = _session(555, object(), 1)
    assert any_active_session([idle, system_sounds, own], own_pid=555) is False
    assert any_active_session([idle, system_sounds, own, browser], own_pid=555) is True
    assert any_active_session([], own_pid=555) is False
