"""Main window: sidebar, navigation and presenter logic for the server."""

from __future__ import annotations

import logging
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from pcremote.domain.errors import DomainError
from pcremote.domain.events import ClientAuthenticated, ClientDisconnected, DevicePaired, DeviceRevoked

from .context import GuiContext
from .qr_image import render_qr, to_ctk_image
from .theme import Theme, apply_appearance, font
from .tray import TrayIcon
from .views.about import AboutView
from .views.home import DEFAULT_PORT, HomeView
from .views.settings import SettingsView

logger = logging.getLogger(__name__)

_NAV_ITEMS = (
    ("Conexión", "connection_icon.png", "home"),
    ("Configuración", "settings_icon.png", "settings"),
    ("Acerca de", "info_icon.png", "about"),
)


class PCRemoteApp(ctk.CTk):
    def __init__(self, ctx: GuiContext, start_hidden: bool = False) -> None:
        apply_appearance()
        super().__init__()
        self._ctx = ctx
        self._theme = Theme()
        self._tray: TrayIcon | None = None

        self.title("PC Remote Control")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=self._theme.dark_bg)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._logo_small = self._load_image("Logo.png", (35, 35))
        self._logo_large = self._load_image("Logo.png", (100, 100))

        self._build_sidebar()
        self._build_content()

        ctx.events.subscribe(ClientAuthenticated, self._on_client_authenticated)
        ctx.events.subscribe(ClientDisconnected, self._on_client_disconnected)
        ctx.events.subscribe(DevicePaired, self._on_devices_changed)
        ctx.events.subscribe(DeviceRevoked, self._on_devices_changed)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        if start_hidden:
            self._hide_to_tray(notify=False)
        if ctx.settings.settings.auto_start_server:
            self.start_server()

    # Assets -------------------------------------------------------------

    def _load_image(self, name: str, size: tuple[int, int]) -> ctk.CTkImage | None:
        path = self._ctx.assets_dir / name
        try:
            img = Image.open(path)
        except (OSError, ValueError):
            logger.debug("Asset not available: %s", path)
            return None
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    # Layout -------------------------------------------------------------

    def _build_sidebar(self) -> None:
        theme = self._theme
        sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=theme.sidebar_bg, border_width=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(6, weight=1)
        sidebar.grid_propagate(False)

        logo_box = ctk.CTkFrame(sidebar, fg_color="transparent", height=100)
        logo_box.pack(fill="x", pady=(20, 30))
        ctk.CTkLabel(
            logo_box,
            text=" PC REMOTE",
            image=self._logo_small,
            compound="left",
            font=font(24, bold=True),
            text_color=theme.text_primary,
        ).pack(pady=(0, 5))
        ctk.CTkLabel(logo_box, text="Control Remoto", font=font(14), text_color=theme.text_secondary).pack()

        ctk.CTkFrame(sidebar, height=1, fg_color=theme.border).pack(fill="x", padx=20, pady=(0, 20))

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for text, icon_name, name in _NAV_ITEMS:
            button = ctk.CTkButton(
                sidebar,
                text=f"  {text}",
                image=self._load_image(icon_name, (20, 20)),
                compound="left",
                command=lambda target=name: self.select_view(target),
                fg_color="transparent",
                hover_color=theme.nav_hover,
                text_color=theme.text_secondary,
                anchor="w",
                font=font(14),
                height=45,
                corner_radius=8,
            )
            button.pack(fill="x", padx=15, pady=5)
            self._nav_buttons[name] = button

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(expand=True, fill="both")
        self._build_status_card(sidebar)

    def _build_status_card(self, sidebar: ctk.CTkFrame) -> None:
        theme = self._theme
        status_card = ctk.CTkFrame(
            sidebar,
            fg_color=theme.card_bg,
            corner_radius=12,
            border_width=1,
            border_color=theme.border,
            height=100,
        )
        status_card.pack(fill="x", padx=15, pady=(0, 20))
        status_card.grid_columnconfigure(0, weight=1)
        status_card.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(status_card, fg_color="transparent")
        content.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")

        self._status_indicator = ctk.CTkFrame(
            content, width=10, height=10, corner_radius=5, fg_color=theme.danger
        )
        self._status_indicator.grid(row=0, column=0, padx=(0, 10))
        self._status_text = ctk.CTkLabel(
            content, text="Servidor detenido", font=font(12, bold=True), text_color=theme.text_primary
        )
        self._status_text.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(content, text="Estado del sistema", font=font(11), text_color=theme.text_secondary).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(5, 0)
        )

    def _build_content(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self._home = HomeView(main, self._theme, self.toggle_server)
        self._settings = SettingsView(
            main, self._theme, self._ctx.autostart, self._ctx.settings, self._ctx.devices, self._ctx.firewall
        )
        self._about = AboutView(main, self._theme, self._ctx.app_version, self._logo_large)
        self._views = {"home": self._home, "settings": self._settings, "about": self._about}
        self.select_view("home")

    def select_view(self, name: str) -> None:
        theme = self._theme
        for key, button in self._nav_buttons.items():
            if key == name:
                button.configure(fg_color=theme.primary, text_color="white", hover_color=theme.secondary)
            else:
                button.configure(fg_color="transparent", text_color=theme.text_secondary, hover_color=theme.nav_hover)
        for view in self._views.values():
            view.grid_forget()
        self._views[name].grid(row=0, column=0, sticky="nsew")

    # Server control -----------------------------------------------------

    def toggle_server(self) -> None:
        if self._ctx.server.running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self) -> None:
        if self._ctx.server.running:
            return
        try:
            port = int(self._home.get_port_text())
        except ValueError:
            port = int(DEFAULT_PORT)
        try:
            info = self._ctx.server.start(port)
        except (DomainError, OSError) as error:
            logger.error("Could not start server: %s", error)
            self._status_text.configure(text="Error al iniciar")
            return

        self._home.set_server_info(info.ip, info.port, info.pin)
        qr = render_qr(self._ctx.server.qr_payload(info), self._ctx.assets_dir / "Logo.png", self._theme)
        self._home.set_qr(to_ctk_image(qr))
        self._home.set_running(True)
        self._status_indicator.configure(fg_color=self._theme.success)
        self._status_text.configure(text="Servidor activo")

    def stop_server(self) -> None:
        if not self._ctx.server.running:
            return
        self._ctx.server.stop()
        self._home.set_running(False)
        self._home.show_waiting()
        self._status_indicator.configure(fg_color=self._theme.danger)
        self._status_text.configure(text="Servidor detenido")

    # Events (arrive on server threads; marshal to the Tk thread) --------

    def _on_client_authenticated(self, event: ClientAuthenticated) -> None:
        self.after(0, lambda: self._home.show_connected(event.device_name))

    def _on_client_disconnected(self, event: ClientDisconnected) -> None:
        if event.was_authenticated:
            self.after(0, self._home.show_waiting)

    def _on_devices_changed(self, _event: DevicePaired | DeviceRevoked) -> None:
        self.after(0, self._settings.refresh_devices)

    # Window lifecycle ---------------------------------------------------

    def on_closing(self) -> None:
        if not self._ctx.settings.settings.minimize_to_tray:
            self.quit_app()
            return
        self._hide_to_tray(notify=True)

    def _hide_to_tray(self, notify: bool) -> None:
        tray = self._ensure_tray()
        if tray is None:
            # No usable tray: minimize instead of hiding so the window can never be lost.
            self.iconify()
            return
        self.withdraw()
        if notify:
            tray.notify("La aplicación sigue ejecutándose en segundo plano.")

    def _ensure_tray(self) -> TrayIcon | None:
        if self._tray is None:
            self._tray = TrayIcon(
                self._ctx.assets_dir / "Logo.png",
                on_show=lambda: self.after(0, self._show_window),
                on_quit=lambda: self.after(0, self.quit_app),
                platform_name=self._ctx.platform_name,
            )
            self._tray.start()
        return self._tray if self._tray.available else None

    def _show_window(self) -> None:
        self.deiconify()
        self.lift()

    def quit_app(self) -> None:
        if self._tray is not None:
            self._tray.stop()
            self._tray = None
        if self._ctx.server.running:
            self._ctx.server.stop()
        self._ctx.auth.release_pin()
        self._ctx.on_exit()
        self.quit()


def run_gui(ctx: GuiContext, start_hidden: bool = False) -> None:
    """Build the main window and block until it is closed.

    With start_hidden the window starts in the system tray (background mode).
    """
    app = PCRemoteApp(ctx, start_hidden)
    app.mainloop()
    try:
        app.destroy()
    except tk.TclError:
        logger.debug("Window already destroyed")

