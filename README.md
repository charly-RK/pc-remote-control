# PC Remote Control

Remote control of a PC (Windows first, with macOS and Linux adapters) from mobile devices, built with Flutter and Python.

## Description

Lets you control your PC remotely from a mobile device (Android/iOS). It includes mouse and keyboard control, media keys and other remote control features.

## Project Structure

```
pc-remote-control/
├── Servidor/          # Python server (Windows first; macOS and Linux adapters)
├── remote_pc/         # Flutter mobile app
└── docs/              # Architecture, protocol and packaging specs
```

## Features

- Remote touchpad, keyboard, media and system controls (shutdown, restart, lock and more, with confirmation)
- Connection through a QR code or the PIN, paired once
- Automatic reconnection: paired devices reconnect with a token and are found by name on the network
- Modern, responsive interface
- Automatic server start, hidden in the system tray
- Keeps running in the background
- Automatic local IP detection

## Requirements

### Server
- Windows 10/11 (macOS and Linux supported through adapters, not yet tested on real machines)
- Python 3.11 or newer
- Local network connection

### Mobile App
- Flutter 3.47 or newer (Dart 3.8+)
- Android 6.0+ (API 23) or iOS 12.0+
- Connection to the same network as the server

## Quick Start

### Server
1. Go to the `Servidor` folder
2. Run the installer or `PCRemoteControl.exe` (if you have already built it)
   - Or install the dependencies (`pip install -r requirements.txt`) and run `python main.py` (`python main.py --background` starts hidden in the tray)

### Mobile App
1. Go to the `remote_pc` folder
2. Run `flutter pub get`
3. Run `flutter analyze` and `flutter test` (optional checks)
4. Run `flutter run`, or `flutter build apk --debug` to build an APK (Gradle 8.14.3, AGP 8.11.1 and Kotlin 2.2.20 are required by Flutter 3.47; do not commit a machine-specific `org.gradle.java.home`)

## Usage

1. Start the server on your PC
2. The server starts automatically and can be minimized to the tray
3. Open the mobile app
4. Scan the QR code shown by the server (or enter the IP, port and PIN by hand) to pair the device once
5. Start controlling your PC. Next time the app reconnects by itself: it uses the saved token, finds the PC by name on the network if its IP changed, and retries with increasing delays if the PC is off or asleep

## Configuration

### Server
- **"Iniciar con Windows"**: enable it in the settings view so the server starts with the system
- **"Minimizar a la bandeja"**: keeps the server running in the background
- **Port**: 5723 by default, adjusted automatically if it is busy
- **Firewall**: allow the port inbound on private networks (administrator rights needed once)
- **Paired devices**: revoke a phone from the settings view

### Mobile App
- Touchpad: tap to click, two-finger tap for right click, two-finger scroll, long press to drag
- Settings: mouse and scroll sensitivity, natural scroll, tap to click, haptics
- Saved PCs: connect, forget and pair again

## Development

See the README.md in each folder for detailed development instructions:
- [Servidor/README.md](Servidor/README.md)
- [docs/PACKAGING.md](docs/PACKAGING.md)

Project rules and specs:
- [AGENTS.md](AGENTS.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/PROTOCOL.md](docs/PROTOCOL.md)

## Technologies

### Server
- Python 3.11+
- Flask + Socket.IO
- CustomTkinter (GUI)
- PyAutoGUI and pynput (input control)

### Mobile App
- Flutter/Dart
- `socket_io_client` (Socket.IO)
- `nsd` (mDNS discovery)
- `mobile_scanner` (QR code scanner)
- `flutter_secure_storage` (pairing token)
- `flutter_background_service` and `flutter_local_notifications` (Android foreground service while connected)
- Provider (state management)

The app keeps the original hand-built interface, organised feature-first under `remote_pc/lib/` (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)).

---

**Developed by RISK KEEP**
