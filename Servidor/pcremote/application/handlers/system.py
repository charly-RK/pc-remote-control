from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.domain.commands import CommandResult, SystemRequest
from pcremote.domain.ports import DesktopController, PowerController


class SystemHandlers:
    def __init__(self, power: PowerController, desktop: DesktopController) -> None:
        self._power = power
        self._desktop = desktop

    def register(self, dispatcher: CommandDispatcher) -> None:
        # 'system' and 'screen' are legacy aliases.
        dispatcher.register(("system_control", "system", "screen"), self.handle)

    def handle(self, data: Mapping[str, Any]) -> CommandResult:
        request = SystemRequest.parse(data)
        if request.power is not None:
            self._power.execute(request.power)
            return CommandResult.success(f"Power action: {request.power.value}")
        if request.desktop is not None:
            self._desktop.execute(request.desktop)
            return CommandResult.success(f"Desktop action: {request.desktop.value}")
        return CommandResult.failure("UNKNOWN_COMMAND", "Unsupported system command")
