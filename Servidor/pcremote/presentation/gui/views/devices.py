"""Paired devices list with revoke action."""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from pcremote.application.device_service import DeviceService
from pcremote.domain.devices import PairedDevice

from ..theme import Theme, font


class DevicesSection(ctk.CTkFrame):
    """Section for the settings card: one row per paired device."""

    def __init__(self, parent: ctk.CTkBaseClass, theme: Theme, devices: DeviceService) -> None:
        super().__init__(parent, fg_color="transparent")
        self._theme = theme
        self._devices = devices
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Dispositivos vinculados", font=font(16, bold=True), text_color=theme.primary).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        self._list = ctk.CTkFrame(self, fg_color="transparent")
        self._list.grid(row=1, column=0, sticky="ew")
        self._list.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self) -> None:
        for widget in self._list.winfo_children():
            widget.destroy()
        devices = self._devices.list_devices()
        if not devices:
            ctk.CTkLabel(
                self._list, text="Sin dispositivos vinculados", font=font(12), text_color=self._theme.text_secondary
            ).grid(row=0, column=0, sticky="w", pady=5)
            return
        for row, device in enumerate(devices):
            self._build_row(row, device)

    def _build_row(self, row: int, device: PairedDevice) -> None:
        theme = self._theme
        item = ctk.CTkFrame(self._list, fg_color=theme.dark_bg, corner_radius=10)
        item.grid(row=row, column=0, sticky="ew", pady=4)
        item.grid_columnconfigure(0, weight=1)

        text_frame = ctk.CTkFrame(item, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        ctk.CTkLabel(text_frame, text=device.name, font=font(14), text_color=theme.text_primary).pack(anchor="w")
        last_seen = datetime.fromtimestamp(device.last_seen).strftime("%d/%m/%Y %H:%M")
        ctk.CTkLabel(
            text_frame, text=f"Última conexión: {last_seen}", font=font(11), text_color=theme.text_secondary
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            item,
            text="Quitar",
            width=80,
            fg_color=theme.danger,
            hover_color=theme.danger_hover,
            command=lambda d=device: self._confirm_revoke(d),
        ).grid(row=0, column=1, padx=15)

    def _confirm_revoke(self, device: PairedDevice) -> None:
        question = f"¿Quitar el dispositivo {device.name}? Tendrá que vincularse de nuevo con el PIN."
        if messagebox.askyesno("Quitar dispositivo", question, parent=self.winfo_toplevel()):
            self._devices.revoke(device.device_id)
            self.refresh()
