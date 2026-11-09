"""Composition root: the only place that instantiates adapters and wires them."""

from __future__ import annotations

import logging
import logging.handlers
import platform
import secrets

from pcremote.application.auth_service import AuthService
from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.application.device_service import DeviceService
from pcremote.application.event_bus import EventBus
from pcremote.application.handlers.keyboard import KeyboardHandlers
from pcremote.application.handlers.media import MediaHandlers
from pcremote.application.handlers.mouse import MouseHandlers
from pcremote.application.handlers.system import SystemHandlers
from pcremote.application.server_controller import ServerController
from pcremote.application.session_registry import SessionRegistry
from pcremote.application.settings_service import SettingsService
from pcremote.infrastructure.input.pyautogui_mouse import PyAutoGuiMouse
from pcremote.infrastructure.input.pynput_keyboard import PynputKeyboard
from pcremote.infrastructure.network.inspector import SocketNetworkInspector
from pcremote.infrastructure.network.zeroconf_discovery import ZeroconfDiscovery
from pcremote.infrastructure.os.startup_registry import build_startup_command
from pcremote.infrastructure.paths import app_data_dir, resource_path
from pcremote.infrastructure.persistence.file_device_repository import FileDeviceRepository
from pcremote.infrastructure.persistence.file_pin_store import FilePinStore
from pcremote.infrastructure.persistence.file_settings_store import FileSettingsStore
from pcremote.infrastructure.platform import PlatformAdapters, create_platform_adapters
from pcremote.presentation.gui.context import GuiContext
from pcremote.presentation.transport.socketio_gateway import SocketIOServer

APP_NAME = "PCRemoteControl"
APP_VERSION = "1.0.0"
PROTOCOL_VERSION = 1


def configure_logging() -> None:
    log_dir = app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.handlers.RotatingFileHandler(
            log_dir / "server.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        ),
        logging.StreamHandler(),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def create_platform() -> PlatformAdapters:
    return create_platform_adapters(APP_NAME, build_startup_command(background=True))


def build_dispatcher(platform_adapters: PlatformAdapters) -> CommandDispatcher:
    dispatcher = CommandDispatcher()
    MouseHandlers(PyAutoGuiMouse()).register(dispatcher)
    KeyboardHandlers(PynputKeyboard()).register(dispatcher)
    MediaHandlers(platform_adapters.media).register(dispatcher)
    SystemHandlers(platform_adapters.power, platform_adapters.desktop).register(dispatcher)
    return dispatcher


def create_context(on_exit) -> GuiContext:  # noqa: ANN001 - simple callback
    platform_adapters = create_platform()
    events = EventBus()
    registry = SessionRegistry()
    data_dir = app_data_dir()
    device_repository = FileDeviceRepository(data_dir / "devices.json")
    settings = SettingsService(FileSettingsStore(data_dir / "settings.json"))
    auth = AuthService(FilePinStore(data_dir / "server_pin.json"), device_repository, events)
    transport = SocketIOServer(
        registry=registry,
        auth=auth,
        dispatcher=build_dispatcher(platform_adapters),
        events=events,
        secret_key=secrets.token_hex(32),
        protocol_version=PROTOCOL_VERSION,
    )
    server = ServerController(
        network=SocketNetworkInspector(),
        transport=transport,
        monitor=platform_adapters.monitor_factory(events),
        auth=auth,
        publisher=events,
        discovery=ZeroconfDiscovery(),
        settings=settings,
    )
    return GuiContext(
        server=server,
        auth=auth,
        events=events,
        autostart=platform_adapters.autostart,
        firewall=platform_adapters.firewall,
        platform_name=platform.system(),
        settings=settings,
        devices=DeviceService(device_repository, events),
        assets_dir=resource_path("src"),
        on_exit=on_exit,
        app_version=APP_VERSION,
    )
