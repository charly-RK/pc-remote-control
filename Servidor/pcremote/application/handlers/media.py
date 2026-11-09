from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.domain.commands import CommandResult, MediaCommand, MediaRequest, MediaState
from pcremote.domain.ports import MediaController

logger = logging.getLogger(__name__)

# Key based commands take a moment to be applied by the OS before the state can be read.
DEFAULT_SETTLE_SECONDS = 0.04
_KEY_BASED = frozenset(
    {
        MediaCommand.PLAY_PAUSE,
        MediaCommand.NEXT,
        MediaCommand.PREVIOUS,
        MediaCommand.VOLUME_UP,
        MediaCommand.VOLUME_DOWN,
        MediaCommand.MUTE,
    }
)


class MediaHandlers:
    def __init__(
        self,
        media: MediaController,
        settle_seconds: float = DEFAULT_SETTLE_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._media = media
        self._settle_seconds = settle_seconds
        self._sleep = sleep

    def register(self, dispatcher: CommandDispatcher) -> None:
        # 'media' is a legacy alias.
        dispatcher.register(("media_control", "media"), self.handle)

    def handle(self, data: Mapping[str, Any]) -> CommandResult:
        request = MediaRequest.parse(data)
        if request.command is MediaCommand.GET_STATE:
            return CommandResult.success("Media state", data=self._read_state().to_dict())
        if request.command is MediaCommand.SET_VOLUME and request.level is not None:
            self._media.set_volume(request.level)
            message = f"Volume set to {round(request.level * 100)}%"
        else:
            self._media.send(request.command)
            if request.command in _KEY_BASED and self._settle_seconds > 0:
                self._sleep(self._settle_seconds)
            message = f"Media command: {request.command.value}"
        return CommandResult.success(message, data=self._read_state().to_dict())

    def _read_state(self) -> MediaState:
        # Reading the state is best effort: it must never fail the command itself.
        try:
            return self._media.get_state()
        except Exception:  # noqa: BLE001 - optional information boundary
            logger.debug("Could not read the media state", exc_info=True)
            return MediaState()
