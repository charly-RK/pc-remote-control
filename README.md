# 🖥️ PC Remote Control

Sistema de control remoto de PC desde dispositivos móviles usando Flutter y Python.

## 📝 Descripción

Aplicación que permite controlar tu PC de forma remota desde un dispositivo móvil (Android/iOS). Incluye control de mouse, teclado, y otras funcionalidades de control remoto.

## 📂 Estructura del Proyecto

```
CONTROL_PC/
├── Servidor/          # Servidor Python para Windows
└── remote_pc/         # Aplicación móvil Flutter
```

## ✨ Características

- 🖱️ Control de mouse y teclado remoto
- 📱 Conexión mediante código QR
- 🔐 Autenticación con PIN
- 🎨 Interfaz moderna y responsive
- 🚀 Inicio automático del servidor
- 📍 Minimización a bandeja del sistema
- 🌐 Detección automática de IP local

## 💻 Requisitos

### Servidor (Windows)
- Windows 10/11
- Python 3.13 o superior
- Conexión a red local

### Aplicación Móvil
- Flutter 3.x
- Android 5.0+ o iOS 12.0+
- Conexión a la misma red que el servidor

## 🚀 Instalación Rápida

### Servidor
1. Navega a la carpeta `Servidor`
2. Ejecuta `PCRemoteControl.exe` (si ya lo has compilado)
   - O instala dependencias y ejecuta `python gui_app.py`

### App Móvil
1. Navega a la carpeta `remote_pc`
2. Ejecuta `flutter pub get`
3. Ejecuta `flutter run`

## 📖 Uso

1. Inicia el servidor en tu PC
2. El servidor se iniciará automáticamente y se minimizará a la bandeja
3. Abre la app móvil
4. Escanea el código QR mostrado en el servidor
5. Ingresa el PIN si se solicita
6. Comienza a controlar tu PC

## ⚙️ Configuración

### Servidor
- **Iniciar con Windows**: Activa esta opción en Configuración para que el servidor se inicie automáticamente
- **Minimizar a la bandeja**: Mantiene el servidor en segundo plano
- **Puerto**: Por defecto 5723, se ajusta automáticamente si está ocupado

### App Móvil
- Configuración de sensibilidad del mouse
- Opciones de conexión
- Gestión de dispositivos guardados

## 📚 Desarrollo

Ver README.md en cada carpeta para instrucciones detalladas de desarrollo:
- [Servidor/README.md](Servidor/README.md)

## 🛠️ Tecnologías

### Servidor
- Python 3.13
- Flask + SocketIO
- CustomTkinter (GUI)
- PyAutoGUI (Control de entrada)

### App Móvil
- Flutter/Dart
- Socket.IO Client
- QR Code Scanner
- Provider (State Management)

---

**Desarrollado por RISK KEEP**
