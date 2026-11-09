"""Media adapter: media keys through pyautogui, absolute volume through pycaw."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from typing import Any

import pyautogui

from pcremote.domain.commands import MediaCommand, MediaState
from pcremote.domain.errors import ExecutionError

logger = logging.getLogger(__name__)

_KEYS: dict[MediaCommand, tuple[str, ...]] = {
    MediaCommand.PLAY_PAUSE: ("playpause",),
    MediaCommand.NEXT: ("nexttrack",),
    MediaCommand.PREVIOUS: ("prevtrack",),
    MediaCommand.VOLUME_UP: ("volumeup",),
    MediaCommand.VOLUME_DOWN: ("volumedown",),
    MediaCommand.MUTE: ("volumemute",),
}

_HOTKEYS: dict[MediaCommand, tuple[str, ...]] = {
    MediaCommand.GAME_BAR: ("win", "g"),
    MediaCommand.RECORD: ("win", "alt", "r"),
    MediaCommand.MIC_MUTE: ("win", "alt", "k"),
}


AUDIO_SESSION_ACTIVE = 1


def any_active_session(sessions: Iterable[Any], own_pid: int | None = None) -> bool:
    """True when some real application (not system sounds, not this app) renders audio."""
    own_pid = os.getpid() if own_pid is None else own_pid
    for session in sessions:
        process_id = getattr(session, "ProcessId", None)
        if getattr(session, "Process", None) is None or not process_id or process_id == own_pid:
            continue
        if getattr(session, "State", None) == AUDIO_SESSION_ACTIVE:
            return True
    return False


class PycawMedia:
    def send(self, command: MediaCommand) -> None:
        try:
            if command in _KEYS:
                pyautogui.press(_KEYS[command][0])
            elif command in _HOTKEYS:
                pyautogui.hotkey(*_HOTKEYS[command])
            else:
                raise ExecutionError(f"Media command not supported by send(): {command.value}")
        except pyautogui.PyAutoGUIException as exc:
            raise ExecutionError(f"Media command failed: {exc}") from exc

    def set_volume(self, level: float) -> None:
        try:
            import pythoncom
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        except ImportError as exc:
            raise ExecutionError("pycaw is not installed, cannot set absolute volume") from exc

        pythoncom.CoInitialize()
        try:
            speakers = AudioUtilities.GetSpeakers()
            interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(level, None)
        except (OSError, AttributeError) as exc:
            logger.warning("Setting volume failed: %s", exc)
            raise ExecutionError(f"Setting volume failed: {exc}") from exc
        finally:
            pythoncom.CoUninitialize()

    def get_state(self) -> MediaState:
        """Best effort: fields that cannot be read stay None."""
        volume, muted = self._read_volume()
        return MediaState(volume=volume, muted=muted, playing=self._read_playing())

    @staticmethod
    def _read_volume() -> tuple[float | None, bool | None]:
        try:
            import pythoncom
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        except ImportError:
            return None, None
        try:
            pythoncom.CoInitialize()
        except Exception:  # noqa: BLE001 - COM initialisation errors vary by build
            return None, None
        try:
            speakers = AudioUtilities.GetSpeakers()
            interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            return round(float(volume.GetMasterVolumeLevelScalar()), 3), bool(volume.GetMute())
        except (OSError, AttributeError, ValueError) as exc:
            logger.debug("Reading volume failed: %s", exc)
            return None, None
        finally:
            pythoncom.CoUninitialize()

    @staticmethod
    def _read_playing() -> bool | None:
        try:
            import pythoncom
            from pycaw.pycaw import AudioUtilities
        except ImportError:
            return None
        try:
            pythoncom.CoInitialize()
        except Exception:  # noqa: BLE001 - COM initialisation errors vary by build
            return None
        try:
            return any_active_session(AudioUtilities.GetAllSessions())
        except (OSError, AttributeError, ValueError) as exc:
            logger.debug("Reading audio sessions failed: %s", exc)
            return None
        finally:
            pythoncom.CoUninitialize()
