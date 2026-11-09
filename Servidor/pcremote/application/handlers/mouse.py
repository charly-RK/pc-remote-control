from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.domain.commands import CommandResult, MouseClick, MouseMove, MouseScroll
from pcremote.domain.ports import MouseController


class MouseHandlers:
    def __init__(self, mouse: MouseController) -> None:
        self._mouse = mouse

    def register(self, dispatcher: CommandDispatcher) -> None:
        dispatcher.register("mouse_move", self.move)
        dispatcher.register("mouse_click", self.click)
        dispatcher.register("mouse_scroll", self.scroll)

    def move(self, data: Mapping[str, Any]) -> CommandResult:
        cmd = MouseMove.parse(data)
        self._mouse.move_relative(cmd.dx, cmd.dy)
        return CommandResult.success()

    def click(self, data: Mapping[str, Any]) -> CommandResult:
        cmd = MouseClick.parse(data)
        self._mouse.click(cmd.button, cmd.click_type)
        return CommandResult.success(f"Mouse {cmd.button.value} {cmd.click_type.value}")

    def scroll(self, data: Mapping[str, Any]) -> CommandResult:
        cmd = MouseScroll.parse(data)
        self._mouse.scroll(cmd.dx, cmd.dy)
        return CommandResult.success()
