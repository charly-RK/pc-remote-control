import customtkinter as ctk
from PIL import Image, ImageTk
import qrcode
import socket
import threading
import os
import sys
import json
import pystray
import winreg

# Importar configuración y servidor
import config
from utils import generate_pin, get_local_ip, NetworkManager, clear_pin
from input_detector import InputDetector

# Configuración de tema mejorada
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_path, relative_path)

class PCRemoteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title("PC Remote Control")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        self.app_flask = None
        self.socketio = None
        self.server_running = False
        self.input_detector = None
        self.server_thread = None
        
        # Paleta de colores profesional
        self.colors = {
            "primary": "#4361ee",
            "secondary": "#3a0ca3",
            "success": "#4cc9f0",
            "danger": "#f72585",
            "warning": "#f8961e",
            "dark_bg": "#111319",  # Más oscuro para mejor contraste
            "card_bg": "#1a1d29",  # El anterior dark_bg ahora es card_bg
            "sidebar_bg": "#0b0d12", # Casi negro
            "border": "#2d3748",     # Color de borde sutil
            "text_primary": "#ffffff",
            "text_secondary": "#94a3b8"
        }
        
        # Configurar background de la ventana principal
        self.configure(fg_color=self.colors["dark_bg"])
        
        # Configurar grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Cargar imágenes
        self.load_images()

        # Crear interfaz
        self.create_sidebar()
        self.create_main_content()
        
        # Inicializar servidor
        self.start_server()

    def load_images(self):
        try:
            self.logo_image = ctk.CTkImage(
                light_image=Image.open(resource_path(os.path.join("src", "Logo.png"))),
                dark_image=Image.open(resource_path(os.path.join("src", "Logo.png"))),
                size=(35, 35)
            )
            self.large_logo_image = ctk.CTkImage(
                light_image=Image.open(resource_path(os.path.join("src", "Logo.png"))),
                dark_image=Image.open(resource_path(os.path.join("src", "Logo.png"))),
                size=(100, 100)
            )
            # Iconos para la barra lateral
            self.home_icon = ctk.CTkImage(
                light_image=Image.open(resource_path(os.path.join("src", "connection_icon.png"))),
                dark_image=Image.open(resource_path(os.path.join("src", "connection_icon.png"))),
                size=(20, 20)
            )
            self.settings_icon = ctk.CTkImage(
                light_image=Image.open(resource_path(os.path.join("src", "settings_icon.png"))),
                dark_image=Image.open(resource_path(os.path.join("src", "settings_icon.png"))),
                size=(20, 20)
            )
            self.about_icon = ctk.CTkImage(
                light_image=Image.open(resource_path(os.path.join("src", "info_icon.png"))),
                dark_image=Image.open(resource_path(os.path.join("src", "info_icon.png"))),
                size=(20, 20)
            )
        except:
            # Iconos por defecto si no existen
            self.home_icon = None
            self.settings_icon = None
            self.about_icon = None

    def create_sidebar(self):
        # Frame de barra lateral
        self.sidebar_frame = ctk.CTkFrame(
            self, 
            width=260, 
            corner_radius=0,
            fg_color=self.colors["sidebar_bg"],
            border_width=0
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        self.sidebar_frame.grid_propagate(False)

        # Logo y título
        self.logo_container = ctk.CTkFrame(
            self.sidebar_frame, 
            fg_color="transparent",
            height=100
        )
        self.logo_container.pack(fill="x", pady=(20, 30))
        
        self.logo_label = ctk.CTkLabel(
            self.logo_container, 
            text=" PC REMOTE", 
            image=self.logo_image,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        self.logo_label.pack(pady=(0, 5))
        
        ctk.CTkLabel(
            self.logo_container,
            text="Control Remoto",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["text_secondary"]
        ).pack()

        # Separador
        ctk.CTkFrame(
            self.sidebar_frame,
            height=1,
            fg_color=self.colors["border"]
        ).pack(fill="x", padx=20, pady=(0, 20))

        # Navegación
        self.nav_buttons = []
        
        nav_items = [
            ("Conexión", self.home_icon, "home"),
            ("Configuración", self.settings_icon, "settings"),
            ("Acerca de", self.about_icon, "about")
        ]
        
        for text, icon, frame_name in nav_items:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=f"  {text}",
                image=icon,
                compound="left",
                command=lambda fn=frame_name: self.select_frame(fn),
                fg_color="transparent",
                hover_color="#2d3748",
                text_color=self.colors["text_secondary"],
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                height=45,
                corner_radius=8
            )
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_buttons.append((btn, frame_name))

        # Espaciador
        ctk.CTkFrame(self.sidebar_frame, fg_color="transparent").pack(expand=True, fill="both")

        # Panel de estado
        status_card = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color=self.colors["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"],
            height=100
        )
        status_card.pack(fill="x", padx=15, pady=(0, 20))
        
        status_card.grid_columnconfigure(0, weight=1)
        status_card.grid_rowconfigure(0, weight=1)
        
        self.status_content = ctk.CTkFrame(status_card, fg_color="transparent")
        self.status_content.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")
        
        self.status_indicator = ctk.CTkFrame(
            self.status_content,
            width=10,
            height=10,
            corner_radius=5,
            fg_color=self.colors["danger"]
        )
        self.status_indicator.grid(row=0, column=0, padx=(0, 10))
        
        self.status_text = ctk.CTkLabel(
            self.status_content,
            text="Servidor detenido",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        self.status_text.grid(row=0, column=1, sticky="w")
        
        ctk.CTkLabel(
            self.status_content,
            text="Estado del sistema",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.colors["text_secondary"]
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

    def create_main_content(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Crear frames de contenido
        self.content_frames = {}
        self.content_frames["home"] = self.create_home_frame()
        self.content_frames["settings"] = self.create_settings_frame()
        self.content_frames["about"] = self.create_about_frame()
        
        # Mostrar frame inicial
        self.select_frame("home")

    def select_frame(self, name):
        # Reset button colors
        for btn, frame_name in self.nav_buttons:
            if frame_name == name:
                btn.configure(
                    fg_color=self.colors["primary"],
                    text_color="white",
                    hover_color=self.colors["secondary"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.colors["text_secondary"],
                    hover_color="#2d3748"
                )

        # Hide all frames
        for frame in self.content_frames.values():
            frame.grid_forget()

        # Show selected frame
        self.content_frames[name].grid(row=0, column=0, sticky="nsew")

    def create_home_frame(self):
        frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="Panel de Conexión",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Configura y gestiona la conexión remota con tu dispositivo",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", pady=(5, 0))

        # Contenido principal en dos columnas
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        # Columna izquierda - Información del servidor
        left_panel = ctk.CTkFrame(
            content, 
            fg_color=self.colors["card_bg"], 
            corner_radius=16,
            border_width=1,
            border_color=self.colors["border"]
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        left_panel.grid_columnconfigure(0, weight=1)

        # Título del panel
        ctk.CTkLabel(
            left_panel,
            text="Configuración del Servidor",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.colors["text_primary"]
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))
        # Campos de configuración
        info_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)

        campos = [
            ("Dirección IP", "ip_label", get_local_ip(), True),
            ("Puerto", "port_entry", "5723", False),
            ("Código PIN", "pin_label", "----", True)
        ]

        for i, (label_text, attr_name, default_value, readonly) in enumerate(campos):
            # Etiqueta
            ctk.CTkLabel(
                info_frame,
                text=label_text,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=self.colors["text_secondary"]
            ).grid(row=i*2, column=0, sticky="w", pady=(15, 5))

            # Campo de entrada
            if attr_name == "ip_label":
                field = ctk.CTkEntry(
                    info_frame,
                    font=ctk.CTkFont(family="Consolas", size=13),
                    height=40,
                    border_width=1,
                    corner_radius=8,
                    fg_color="#1a1d29",
                    border_color="#3a3f5d"
                )
                field.insert(0, default_value)
                field.configure(state="readonly")
                self.ip_label = field
            elif attr_name == "port_entry":
                field = ctk.CTkEntry(
                    info_frame,
                    font=ctk.CTkFont(family="Consolas", size=13),
                    height=40,
                    border_width=1,
                    corner_radius=8
                )
                field.insert(0, default_value)
                self.port_entry = field
            else:  # pin_label
                field = ctk.CTkEntry(
                    info_frame,
                    font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
                    height=40,
                    border_width=1,
                    corner_radius=8,
                    fg_color="#1a1d29",
                    border_color="#3a3f5d"
                )
                field.insert(0, default_value)
                field.configure(state="readonly")
                self.pin_label = field

            field.grid(row=i*2+1, column=0, sticky="ew", pady=(0, 10))

        # Botón de control
        button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(20, 30))

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="INICIAR SERVIDOR",
            command=self.toggle_server,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=self.colors["primary"],
            hover_color=self.colors["secondary"],
            border_width=0
        )
        self.start_btn.pack(fill="x")

        # Columna derecha - Contenedor dinámico
        self.right_panel = ctk.CTkFrame(
            content, 
            fg_color=self.colors["card_bg"], 
            corner_radius=16,
            border_width=1,
            border_color=self.colors["border"]
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)

        # Contenedor para el contenido cambiante (QR o Estado Conectado)
        self.qr_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.qr_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.qr_container.grid_columnconfigure(0, weight=1)
        self.qr_container.grid_rowconfigure(0, weight=1)

        # Mostrar vista inicial
        self.show_qr_view()

        return frame

    def show_qr_view(self):
        # Limpiar contenedor
        for widget in self.qr_container.winfo_children():
            widget.destroy()

        # Frame interno centrado
        inner_frame = ctk.CTkFrame(self.qr_container, fg_color="transparent")
        inner_frame.grid(row=0, column=0)

        # Título
        ctk.CTkLabel(
            inner_frame,
            text="Código QR de Conexión",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(pady=(0, 20))

        # QR Image
        self.qr_label = ctk.CTkLabel(inner_frame, text="")
        self.qr_label.pack()
        
        # Restaurar imagen si existe
        if hasattr(self, 'last_qr_image') and self.last_qr_image:
            self.qr_label.configure(image=self.last_qr_image)

        # Texto debajo del QR
        ctk.CTkLabel(
            inner_frame,
            text="Escanea para conectar",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(15, 0))

        # Panel de ayuda
        help_frame = ctk.CTkFrame(
            inner_frame,
            fg_color="#1a1d29",
            corner_radius=12
        )
        help_frame.pack(fill="x", pady=(30, 0))

        ctk.CTkLabel(
            help_frame,
            text="💡 Instrucciones Rápidas",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 5))

        instructions = [
            "1. Inicia el servidor",
            "2. Escanea el código QR",
            "3. Introduce el PIN si se solicita"
        ]
        
        for i, text in enumerate(instructions):
            ctk.CTkLabel(
                help_frame,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=self.colors["text_secondary"]
            ).pack(anchor="w", padx=15, pady=(0, 5 if i == len(instructions)-1 else 2))

    def show_connected_view(self, device_name="Dispositivo"):
        # Limpiar contenedor
        for widget in self.qr_container.winfo_children():
            widget.destroy()

        # Frame interno centrado
        inner_frame = ctk.CTkFrame(self.qr_container, fg_color="transparent")
        inner_frame.grid(row=0, column=0)

        # Icono de conexión exitosa
        ctk.CTkLabel(
            inner_frame,
            text="📱",
            font=ctk.CTkFont(size=64)
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            inner_frame,
            text="¡Dispositivo Conectado!",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=self.colors["success"]
        ).pack()

        ctk.CTkLabel(
            inner_frame,
            text=f"Conectado a: {device_name}",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(10, 30))

        # Estado
        status_frame = ctk.CTkFrame(inner_frame, fg_color="#1a1d29", corner_radius=10)
        status_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(
            status_frame,
            text="🟢 Conexión Estable",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.colors["success"]
        ).pack(pady=15)

    def on_client_connected(self, device_name):
        self.after(0, lambda: self.show_connected_view(device_name))

    def on_client_disconnected(self):
        self.after(0, self.show_qr_view)

    def create_settings_frame(self):
        frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="Configuración del Sistema",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Personaliza el comportamiento de la aplicación",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", pady=(5, 0))

        # Tarjeta de configuraciones
        card = ctk.CTkFrame(
            frame, 
            fg_color=self.colors["card_bg"], 
            corner_radius=16,
            border_width=1,
            border_color=self.colors["border"]
        )
        card.pack(fill="both", expand=True)

        # Secciones de configuración
        sections = [
            ("General", [
                ("Iniciar con Windows", "Ejecutar al iniciar el sistema"),
                ("Minimizar a la bandeja", "No cerrar al hacer clic en X"),
                ("Iniciar servidor automáticamente", "Al abrir la aplicación")
            ]),
            # ("Conexión", [
            #     ("Notificaciones de conexión", "Mostrar alertas al conectar"),
            #     ("Reintentos automáticos", "Reconectar automáticamente"),
            #     ("Timeout de conexión (30s)", "Tiempo máximo de espera")
            # ]),
            # ("Interfaz", [
            #     ("Modo Oscuro", "Tema oscuro activado"),
            #     ("Mostrar estadísticas", "Panel de rendimiento"),
            #     ("Animaciones suaves", "Transiciones fluidas")
            # ])
        ]

        row_offset = 0
        for section_idx, (section_title, options) in enumerate(sections):
            # Título de sección
            ctk.CTkLabel(
                card,
                text=section_title,
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                text_color=self.colors["primary"]
            ).grid(row=row_offset, column=0, sticky="w", padx=30, pady=(30 if section_idx == 0 else 40, 15))

            row_offset += 1

            # Opciones de configuración
            for i, (option_text, description) in enumerate(options):
                option_frame = ctk.CTkFrame(card, fg_color="transparent")
                option_frame.grid(row=row_offset, column=0, sticky="ew", padx=30, pady=5)
                option_frame.grid_columnconfigure(0, weight=1)

                # Texto de la opción
                text_frame = ctk.CTkFrame(option_frame, fg_color="transparent")
                text_frame.grid(row=0, column=0, sticky="w")

                ctk.CTkLabel(
                    text_frame,
                    text=option_text,
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    text_color=self.colors["text_primary"]
                ).pack(anchor="w")

                ctk.CTkLabel(
                    text_frame,
                    text=description,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=self.colors["text_secondary"]
                ).pack(anchor="w", pady=(2, 0))

                # Switch
                switch = ctk.CTkSwitch(
                    option_frame,
                    text="",
                    width=50,
                    button_color=self.colors["primary"],
                    progress_color="#2d3748"
                )
                switch.grid(row=0, column=1, padx=(20, 0))
                
                # Configurar switches específicos
                if option_text == "Iniciar con Windows":
                    self.startup_switch = switch
                    switch.configure(command=self.toggle_startup)
                    # Estado inicial se verificará después de definir los métodos
                    self.after(100, lambda s=switch: s.select() if self.check_startup_status() else s.deselect())
                elif option_text == "Minimizar a la bandeja":
                    self.tray_switch = switch
                    switch.select()
                elif section_idx == 2 and i == 0: # Modo oscuro
                    switch.select()

                row_offset += 1

        return frame

    def create_about_frame(self):
        frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        
        # Card principal centrada
        main_card = ctk.CTkFrame(
            frame, 
            fg_color=self.colors["card_bg"], 
            corner_radius=20,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_card.grid(row=0, column=0, sticky="nsew", padx=100, pady=50)
        main_card.grid_columnconfigure(0, weight=1)
        main_card.grid_rowconfigure(1, weight=1)

        # Header con logo
        header = ctk.CTkFrame(main_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(50, 0))

        # Logo grande centrado
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack()

        if hasattr(self, 'large_logo_image'):
            logo = ctk.CTkLabel(logo_frame, text="", image=self.large_logo_image)
            logo.pack(pady=(0, 20))

        # Título
        ctk.CTkLabel(
            header,
            text="PC Remote Control",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack()

        ctk.CTkLabel(
            header,
            text="v1.0.0",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["primary"]
        ).pack(pady=(5, 0))

        # Contenido
        content = ctk.CTkFrame(main_card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=50, pady=30)

        # Descripción
        desc_text = (
            "Aplicación de control remoto avanzada que te permite "
            "gestionar tu PC desde cualquier dispositivo móvil. "
        )
        
        desc = ctk.CTkLabel(
            content,
            text=desc_text,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["text_secondary"],
            wraplength=500,
            justify="center"
        )
        desc.pack(pady=(0, 30))

        # # Características
        # features_frame = ctk.CTkFrame(content, fg_color="#1a1d29", corner_radius=12)
        # features_frame.pack(fill="x", pady=(0, 30), padx=20)

        # features = [
        #     ("🚀", "Conexión rápida y estable"),
        #     ("🔐", "Seguridad con autenticación PIN"),
        #     ("📱", "Interfaz optimizada para móviles"),
        #     ("⚡", "Bajo consumo de recursos")
        # ]

        # for icon, text in features:
        #     feature = ctk.CTkFrame(features_frame, fg_color="transparent")
        #     feature.pack(fill="x", padx=20, pady=10)
        #     
        #     ctk.CTkLabel(
        #         feature,
        #         text=icon,
        #         font=ctk.CTkFont(size=20)
        #     ).pack(side="left", padx=(0, 15))
        #     
        #     ctk.CTkLabel(
        #         feature,
        #         text=text,
        #         font=ctk.CTkFont(family="Segoe UI", size=13),
        #         text_color=self.colors["text_primary"]
        #     ).pack(side="left")

        # # Información técnica
        # info_frame = ctk.CTkFrame(content, fg_color="transparent")
        # info_frame.pack(fill="x", pady=(0, 20))

        # tech_info = [
        #     ("Desarrollado con:", "Python, CustomTkinter, Flask-SocketIO"),
        #     ("Compatibilidad:", "Windows 10/11, Android, iOS"),
        #     ("Licencia:", "Propietario - Uso personal")
        # ]

        # for label, value in tech_info:
        #     item = ctk.CTkFrame(info_frame, fg_color="transparent")
        #     item.pack(fill="x", pady=8)
        #     
        #     ctk.CTkLabel(
        #         item,
        #         text=label,
        #         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        #         text_color=self.colors["text_secondary"],
        #         width=120
        #     ).pack(side="left", anchor="w")
        #         #     ctk.CTkLabel(
        #         item,
        #         text=value,
        #         font=ctk.CTkFont(family="Segoe UI", size=12),
        #         text_color=self.colors["text_primary"]
        #     ).pack(side="left", anchor="w")

        # Footer
        footer = ctk.CTkFrame(main_card, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", pady=(0, 30))
        ctk.CTkLabel(
            footer,
            text="PC Remote Control - Desarrollador RISK KEEP",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.colors["text_secondary"]
        ).pack()

        return frame

    def generate_qr(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Crear imagen con estilo moderno
        img = qr.make_image(fill_color=self.colors["primary"], back_color=self.colors["card_bg"])
        img = img.convert("RGB")
        
        # Agregar logo en el centro si existe
        try:
            logo_path = resource_path(os.path.join("src", "Logo.png"))
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                # Reducir tamaño del logo para no tapar demasiado (15% del ancho)
                logo_size = int(img.size[0] * 0.15)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Posicionar logo en el centro
                pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
                
                # Crear fondo para el logo para mejor contraste
                logo_bg = Image.new('RGB', (logo_size + 4, logo_size + 4), self.colors["card_bg"])
                img.paste(logo_bg, (pos[0] - 2, pos[1] - 2))
                
                img.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            print(f"Error agregando logo al QR: {e}")
        
        return ctk.CTkImage(light_image=img, dark_image=img, size=(220, 220))

    def toggle_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        if self.server_running:
            return

        try:
            # Configurar variables
            config.PIN_CODE = generate_pin()
            config.SERVER_IP = get_local_ip()
            
            # Gestión de puertos
            nm = NetworkManager(default_port=int(self.port_entry.get()))
            port = nm.get_available_port()
            config.SERVER_PORT = port
            
            # Actualizar UI con el puerto real
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, str(port))
            
            # Actualizar UI
            self.pin_label.configure(state="normal")
            self.pin_label.delete(0, "end")
            self.pin_label.insert(0, config.PIN_CODE)
            self.pin_label.configure(state="readonly")
            
            # Generar QR
            qr_data = json.dumps({
                "ip": config.SERVER_IP,
                "code": config.PIN_CODE,
                "port": port
            })
            qr_img = self.generate_qr(qr_data)
            self.last_qr_image = qr_img
            
            if hasattr(self, 'qr_label') and self.qr_label.winfo_exists():
                self.qr_label.configure(image=qr_img)
            
            # Iniciar servidor Flask
            self.app_flask = config.create_app()
            self.socketio = config.create_socketio(self.app_flask)
            
            from socket_handlers import setup_socket_handlers
            from routes import setup_routes
            
            setup_socket_handlers(
                self.socketio,
                on_auth_success=self.on_client_connected,
                on_disconnect=self.on_client_disconnected
            )
            setup_routes(self.app_flask)
            
            # Iniciar InputDetector
            self.input_detector = InputDetector(self.socketio)
            self.input_detector.start()
            
            # Hilo del servidor
            self.server_thread = threading.Thread(target=self._run_server, args=(port,), daemon=True)
            self.server_thread.start()
            
            self.server_running = True
            self.start_btn.configure(
                text="DETENER SERVIDOR", 
                fg_color=self.colors["danger"],
                hover_color="#c0392b"
            )
            self.status_indicator.configure(fg_color=self.colors["success"])
            self.status_text.configure(text="Servidor activo")
            
        except Exception as e:
            print(f"Error starting server: {e}")
            self.status_text.configure(text=f"Error: {str(e)[:30]}...")

    def _run_server(self, port):
        try:
            self.socketio.run(
                self.app_flask,
                host='0.0.0.0',
                port=port,
                debug=False,
                use_reloader=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            print(f"Server thread error: {e}")

    def stop_server(self):
        if not self.server_running:
            return
            
        if self.input_detector:
            self.input_detector.stop()
            
        self.server_running = False
        self.start_btn.configure(
            text="INICIAR SERVIDOR", 
            fg_color=self.colors["primary"],
            hover_color=self.colors["secondary"]
        )
        self.status_indicator.configure(fg_color=self.colors["danger"])
        self.status_text.configure(text="Servidor detenido")

    def setup_tray_icon(self):
        try:
            icon_path = resource_path(os.path.join("src", "Logo.png"))
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
            else:
                raise Exception("Logo not found")
        except:
            # Fallback image
            image = Image.new('RGB', (64, 64), color = (67, 97, 238))
            
        def on_show(icon, item):
            self.after(0, self.deiconify)

        def on_quit(icon, item):
            self.after(0, self.quit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Mostrar", on_show, default=True),
            pystray.MenuItem("Salir", on_quit)
        )
        
        self.tray_icon = pystray.Icon("PC Remote", image, "PC Remote Control", menu)
        
        # Run in separate thread to not block GUI
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def quit_app(self, *args):
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
        
        if self.input_detector:
            self.input_detector.stop()
            
        # Limpiar PIN al cerrar completamente
        clear_pin()
            
        self.quit()
        sys.exit(0)

    def check_startup_status(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "PCRemoteControl")
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if self.startup_switch.get():
                # Add to registry
                if getattr(sys, 'frozen', False):
                    # Running as compiled exe
                    app_path = f'"{sys.executable}"'
                else:
                    # Running as script (pythonw.exe for no console)
                    script_path = os.path.realpath(__file__)
                    # Use pythonw.exe if available to avoid console window on startup
                    python_exe = sys.executable.replace("python.exe", "pythonw.exe")
                    if not os.path.exists(python_exe):
                        python_exe = sys.executable
                    app_path = f'"{python_exe}" "{script_path}"'
                    
                winreg.SetValueEx(key, "PCRemoteControl", 0, winreg.REG_SZ, app_path)
            else:
                # Remove from registry
                try:
                    winreg.DeleteValue(key, "PCRemoteControl")
                except WindowsError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error modifying registry: {e}")

    def on_closing(self):
        # Check if minimize to tray is enabled
        minimize_to_tray = False
        if hasattr(self, 'tray_switch') and self.tray_switch.get():
            minimize_to_tray = True
            
        if minimize_to_tray:
            self.withdraw()
            if not hasattr(self, 'tray_icon') or not self.tray_icon:
                self.setup_tray_icon()
            
            # Show notification if supported (optional)
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.notify(
                    "La aplicación sigue ejecutándose en segundo plano.",
                    "PC Remote Control"
                )
        else:
            self.quit_app()

if __name__ == "__main__":
    app = PCRemoteApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()