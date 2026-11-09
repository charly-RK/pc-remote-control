"""Settings row that shows the firewall status and lets the user configure it."""

from __future__ import annotations

import logging
import threading

import customtkinter as ctk

from pcremote.domain.ports import FirewallManager

from ..theme import Theme, font

logger = logging.getLogger(__name__)


class FirewallRow(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, theme: Theme, firewall: FirewallManager) -> None:
        super().__init__(parent, fg_color="transparent")
        self._theme = theme
        self._firewall = firewall
        self.grid_columnconfigure(0, weight=1)

        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            text_frame, text="Permitir conexiones en el firewall", font=font(14), text_color=theme.text_primary
        ).pack(anchor="w")
        self._status = ctk.CTkLabel(text_frame, text="", font=font(11), text_color=theme.text_secondary)
        self._status.pack(anchor="w", pady=(2, 0))

        self._button = ctk.CTkButton(
            self,
            text="Configurar",
            width=110,
            command=self._on_configure,
            fg_color=theme.primary,
            hover_color=theme.secondary,
            font=font(13, bold=True),
        )
        self._button.grid(row=0, column=1, padx=(20, 0))
        self.refresh()

    def refresh(self, failed: bool = False) -> None:
        try:
            configured = self._firewall.is_configured()
        except OSError:
            logger.warning("Could not read firewall status", exc_info=True)
            configured = False
        if configured:
            self._status.configure(text="Configurado", text_color=self._theme.success)
            self._button.grid_remove()
            return
        text = "No se pudo configurar" if failed else "No configurado"
        self._status.configure(text=text, text_color=self._theme.danger)
        self._button.configure(state="normal")
        self._button.grid()

    def _on_configure(self) -> None:
        self._button.configure(state="disabled")
        threading.Thread(target=self._configure_in_background, daemon=True).start()

    def _configure_in_background(self) -> None:
        try:
            ok = self._firewall.configure()
        except OSError:
            logger.exception("Firewall configuration failed")
            ok = False
        try:
            self.after(0, lambda: self.refresh(failed=not ok))
        except RuntimeError:
            logger.debug("Window closed before the firewall result arrived")
