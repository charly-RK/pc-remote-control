"""Settings view."""

from __future__ import annotations

import logging

import customtkinter as ctk

from pcremote.application.device_service import DeviceService
from pcremote.application.settings_service import SettingsService
from pcremote.domain.ports import AutoStartManager, FirewallManager

from ..theme import Theme, card, font
from .devices import DevicesSection
from .firewall_row import FirewallRow

logger = logging.getLogger(__name__)

_OPTIONS = (
    ("startup", "Iniciar con el sistema", "Ejecutar al iniciar el sistema"),
    ("tray", "Minimizar a la bandeja", "No cerrar al hacer clic en X"),
    ("auto_start", "Iniciar servidor automáticamente", "Al abrir la aplicación"),
)


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        theme: Theme,
        autostart: AutoStartManager,
        settings: SettingsService,
        devices: DeviceService,
        firewall: FirewallManager,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._theme = theme
        self._autostart = autostart
        self._settings = settings
        self._devices_service = devices
        self._firewall = firewall
        self._switches: dict[str, ctk.CTkSwitch] = {}

        self._build_header()
        self._build_card()
        self._build_devices_card()
        self._load_initial_state()

    def refresh_devices(self) -> None:
        self._devices_section.refresh()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            header, text="Configuración del Sistema", font=font(28, bold=True), text_color=self._theme.text_primary
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Personaliza el comportamiento de la aplicación",
            font=font(14),
            text_color=self._theme.text_secondary,
        ).pack(anchor="w", pady=(5, 0))

    def _build_card(self) -> None:
        theme = self._theme
        panel = card(self, theme)
        panel.pack(fill="both", expand=True)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel, text="General", font=font(16, bold=True), text_color=theme.primary).grid(
            row=0, column=0, sticky="w", padx=30, pady=(30, 15)
        )
        for row, (key, title, description) in enumerate(_OPTIONS, start=1):
            self._build_option(panel, row, key, title, description)
        FirewallRow(panel, theme, self._firewall).grid(
            row=len(_OPTIONS) + 1, column=0, sticky="ew", padx=30, pady=(5, 30)
        )

    def _build_devices_card(self) -> None:
        panel = card(self, self._theme)
        panel.pack(fill="both", expand=True, pady=(20, 0))
        panel.grid_columnconfigure(0, weight=1)
        self._devices_section = DevicesSection(panel, self._theme, self._devices_service)
        self._devices_section.grid(row=0, column=0, sticky="ew", padx=30, pady=30)

    def _build_option(self, parent: ctk.CTkFrame, row: int, key: str, title: str, description: str) -> None:
        theme = self._theme
        option = ctk.CTkFrame(parent, fg_color="transparent")
        option.grid(row=row, column=0, sticky="ew", padx=30, pady=5)
        option.grid_columnconfigure(0, weight=1)

        text_frame = ctk.CTkFrame(option, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(text_frame, text=title, font=font(14), text_color=theme.text_primary).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=description, font=font(11), text_color=theme.text_secondary).pack(
            anchor="w", pady=(2, 0)
        )

        switch = ctk.CTkSwitch(
            option, text="", width=50, button_color=theme.primary, progress_color=theme.switch_progress
        )
        switch.grid(row=0, column=1, padx=(20, 0))
        self._switches[key] = switch

    def _load_initial_state(self) -> None:
        current = self._settings.settings
        for key, enabled in (("tray", current.minimize_to_tray), ("auto_start", current.auto_start_server)):
            switch = self._switches[key]
            if enabled:
                switch.select()
            else:
                switch.deselect()
        self._switches["tray"].configure(command=lambda: self._persist("minimize_to_tray", "tray"))
        self._switches["auto_start"].configure(command=lambda: self._persist("auto_start_server", "auto_start"))
        startup = self._switches["startup"]
        try:
            if self._autostart.is_enabled():
                startup.select()
        except OSError:
            logger.warning("Could not read startup registration", exc_info=True)
        startup.configure(command=self._on_startup_toggled)

    def _persist(self, field: str, key: str) -> None:
        self._settings.update(**{field: bool(self._switches[key].get())})

    def _on_startup_toggled(self) -> None:
        switch = self._switches["startup"]
        enabled = bool(switch.get())
        try:
            self._autostart.set_enabled(enabled)
        except OSError:
            logger.exception("Could not update startup registration")
            switch.deselect() if enabled else switch.select()
