"""Connection panel: server fields, start/stop button and QR / connected state."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from ..theme import Theme, card, font

DEFAULT_PORT = "5723"


class HomeView(ctk.CTkScrollableFrame):
    def __init__(self, parent: ctk.CTkBaseClass, theme: Theme, on_toggle_server: Callable[[], None]) -> None:
        super().__init__(parent, fg_color="transparent")
        self._theme = theme
        self._on_toggle_server = on_toggle_server
        self._qr_image: ctk.CTkImage | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        self._build_server_panel(content)
        self._build_right_panel(content)
        self.show_waiting()

    # Public API ---------------------------------------------------------

    def get_port_text(self) -> str:
        return self._port_entry.get().strip()

    def set_server_info(self, ip: str, port: int, pin: str) -> None:
        self._set_readonly(self._ip_entry, ip)
        self._port_entry.delete(0, "end")
        self._port_entry.insert(0, str(port))
        self._set_readonly(self._pin_entry, pin)

    def set_qr(self, image: ctk.CTkImage | None) -> None:
        self._qr_image = image
        if hasattr(self, "_qr_label") and self._qr_label.winfo_exists():
            self._qr_label.configure(image=image)

    def set_running(self, running: bool) -> None:
        theme = self._theme
        if running:
            self._start_btn.configure(
                text="DETENER SERVIDOR", fg_color=theme.danger, hover_color=theme.danger_hover
            )
        else:
            self._start_btn.configure(
                text="INICIAR SERVIDOR", fg_color=theme.primary, hover_color=theme.secondary
            )

    def show_waiting(self) -> None:
        inner = self._reset_right_panel()
        theme = self._theme

        ctk.CTkLabel(
            inner, text="Código QR de Conexión", font=font(18, bold=True), text_color=theme.text_primary
        ).pack(pady=(0, 20))

        self._qr_label = ctk.CTkLabel(inner, text="", image=self._qr_image)
        self._qr_label.pack()

        ctk.CTkLabel(
            inner, text="Escanea para conectar", font=font(12), text_color=theme.text_secondary
        ).pack(pady=(15, 0))

        help_frame = ctk.CTkFrame(inner, fg_color=theme.card_bg, corner_radius=12)
        help_frame.pack(fill="x", pady=(30, 0))
        ctk.CTkLabel(
            help_frame, text="Instrucciones Rápidas", font=font(13, bold=True), text_color=theme.text_primary
        ).pack(anchor="w", padx=15, pady=(15, 5))

        steps = ["1. Inicia el servidor", "2. Escanea el código QR", "3. Introduce el PIN si se solicita"]
        for index, text in enumerate(steps):
            ctk.CTkLabel(help_frame, text=text, font=font(12), text_color=theme.text_secondary).pack(
                anchor="w", padx=15, pady=(0, 5 if index == len(steps) - 1 else 2)
            )

    def show_connected(self, device_name: str = "Dispositivo") -> None:
        inner = self._reset_right_panel()
        theme = self._theme

        ctk.CTkLabel(
            inner, text="Dispositivo Conectado", font=font(20, bold=True), text_color=theme.success
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner, text=f"Conectado a: {device_name}", font=font(14), text_color=theme.text_secondary
        ).pack(pady=(0, 30))

        status = ctk.CTkFrame(inner, fg_color=theme.card_bg, corner_radius=10)
        status.pack(fill="x", padx=20)
        ctk.CTkLabel(
            status, text="Conexión Estable", font=font(13, bold=True), text_color=theme.success
        ).pack(pady=15)

    # Construction -------------------------------------------------------

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(
            header, text="Panel de Conexión", font=font(28, bold=True), text_color=self._theme.text_primary
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Configura y gestiona la conexión remota con tu dispositivo",
            font=font(14),
            text_color=self._theme.text_secondary,
        ).pack(anchor="w", pady=(5, 0))

    def _build_server_panel(self, content: ctk.CTkFrame) -> None:
        theme = self._theme
        panel = card(content, theme)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel, text="Configuración del Servidor", font=font(18, bold=True), text_color=theme.text_primary
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))

        fields = ctk.CTkFrame(panel, fg_color="transparent")
        fields.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        fields.grid_columnconfigure(0, weight=1)

        self._ip_entry = self._add_field(fields, 0, "Dirección IP", "----", readonly=True)
        self._port_entry = self._add_field(fields, 1, "Puerto", DEFAULT_PORT, readonly=False)
        self._pin_entry = self._add_field(fields, 2, "Código PIN", "----", readonly=True, size=15, bold=True)

        button_frame = ctk.CTkFrame(panel, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(20, 30))
        self._start_btn = ctk.CTkButton(
            button_frame,
            text="INICIAR SERVIDOR",
            command=self._on_toggle_server,
            font=font(14, bold=True),
            height=45,
            corner_radius=10,
            fg_color=theme.primary,
            hover_color=theme.secondary,
            border_width=0,
        )
        self._start_btn.pack(fill="x")

    def _add_field(
        self,
        parent: ctk.CTkFrame,
        index: int,
        label: str,
        value: str,
        readonly: bool,
        size: int = 13,
        bold: bool = False,
    ) -> ctk.CTkEntry:
        theme = self._theme
        ctk.CTkLabel(parent, text=label, font=font(13, bold=True), text_color=theme.text_secondary).grid(
            row=index * 2, column=0, sticky="w", pady=(15, 5)
        )
        options: dict = {}
        if readonly:
            options = {"fg_color": theme.input_bg, "border_color": theme.input_border}
        entry = ctk.CTkEntry(
            parent, font=font(size, bold=bold, mono=True), height=40, border_width=1, corner_radius=8, **options
        )
        entry.insert(0, value)
        if readonly:
            entry.configure(state="readonly")
        entry.grid(row=index * 2 + 1, column=0, sticky="ew", pady=(0, 10))
        return entry

    def _build_right_panel(self, content: ctk.CTkFrame) -> None:
        panel = card(content, self._theme)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        self._right_container = ctk.CTkFrame(panel, fg_color="transparent")
        self._right_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self._right_container.grid_columnconfigure(0, weight=1)
        self._right_container.grid_rowconfigure(0, weight=1)

    def _reset_right_panel(self) -> ctk.CTkFrame:
        for widget in self._right_container.winfo_children():
            widget.destroy()
        inner = ctk.CTkFrame(self._right_container, fg_color="transparent")
        inner.grid(row=0, column=0)
        return inner

    @staticmethod
    def _set_readonly(entry: ctk.CTkEntry, value: str) -> None:
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.configure(state="readonly")
