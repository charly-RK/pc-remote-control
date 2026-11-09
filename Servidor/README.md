# PC Remote Control Server

Python server (Windows first; macOS and Linux through per-OS adapters) that allows remote control of the PC from mobile devices.

## Features

- Flask server with Socket.IO for real-time communication
- Modern GUI built with CustomTkinter
- Automatic QR code generation for connection
- One-time pairing with the PIN; paired devices reconnect with a token (no PIN, no QR) and can be revoked
- Automatic discovery on the local network (mDNS), so an IP change does not break reconnection
- PIN and token attempts are rate limited per IP
- Mouse, keyboard, media and system control
- Start with Windows, hidden in the system tray (`--background`)
- Runs in the background with the window closed
- Automatic IP and free port detection

## Requirements

- Windows 10/11 (macOS 12+ and Linux with X11 are supported by adapters that have not been tested on real machines yet)
- Python 3.11 or newer
- Linux system packages: `python3-tk`, `xdotool`, `playerctl` (see [../docs/PACKAGING.md](../docs/PACKAGING.md))

## Installation

### Option 1: Build and use the executable

1. Build the executable (or use the installer from `installer/windows/`). Open a terminal in the `Servidor` folder and run:
   ```bash
   python build.py
   ```
   (this runs `PyInstaller` with `PCRemoteControl.spec`)

2. Run it:
   - Go to the generated `dist/` folder
   - Run `PCRemoteControl.exe`

3. The server starts automatically and can be minimized to the system tray.

### Option 2: Run from source (recommended for development)

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   For development tools (tests and linting):
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run the application (GUI and server):
   ```bash
   python main.py
   ```
   To start hidden in the system tray (this is what the autostart entry runs):
   ```bash
   python main.py --background
   ```
   To allow the application through the Windows firewall without the installer (needs administrator rights, accept the prompt):
   ```bash
   python main.py --configure-firewall
   ```
   (`--remove-firewall` removes the rule.)

## Usage

### First time

1. Start the application (from source or the compiled executable)
2. The server starts automatically
3. A QR code appears in the interface
4. Scan the QR code from the mobile app (or enter the PIN shown in the interface)
5. The device is paired. From then on it reconnects by itself, even after the PC or the app restarts

### Settings

Open the "Configuración" section of the interface to:

- **"Iniciar con el sistema"**: the application runs when the system starts (registry entry on Windows, LaunchAgent on macOS, XDG autostart on Linux)
- **"Minimizar a la bandeja"**: keeps the server running in the background instead of closing
- **"Iniciar servidor automáticamente"**: the server starts when the application opens
- **Firewall** (Windows): shows whether the rule exists and a "Configurar" button that creates it (asks for administrator rights)
- **Paired devices**: list of paired phones; revoke one to cut its access immediately

Settings are saved in `%APPDATA%/PCRemoteControl/settings.json`; paired devices in `devices.json` (only token hashes). Only one instance of the application can run at a time.

### System tray

When the application is minimized to the tray:
- Right-click the icon to see the options
- "Mostrar" opens the interface
- "Salir" closes the application completely

## Project Structure

```
Servidor/
├── main.py                 # Entry point (starts the GUI and the server)
├── pcremote/               # Application package
│   ├── bootstrap.py        # Composition root (wires adapters and services)
│   ├── domain/             # Pure Python: commands, errors, events, ports, session, devices, settings
│   ├── application/        # Auth and pairing, devices, settings, command dispatcher, handlers, server controller
│   ├── infrastructure/     # Adapters: platform/ (Windows, macOS, Linux), input, audio, power, file stores, network, mDNS, firewall
│   └── presentation/       # Socket.IO gateway, HTTP routes, GUI
├── tests/                  # Unit and contract tests
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Development dependencies
├── PCRemoteControl.spec    # PyInstaller configuration (platform-aware)
├── installer/              # Windows Inno Setup script, macOS and Linux notes
├── src/                    # Resources (icons, images)
├── dist/                   # Compiled executable (not included in the repo)
└── build/                  # Build files (not included in the repo)
```

See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the architecture and [../docs/PROTOCOL.md](../docs/PROTOCOL.md) for the Socket.IO contract.

## Building the Executable

To generate a new executable after changing the code:

### Step 1: Install or update dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Build with the .spec file

Use the `PCRemoteControl.spec` file, which is already configured with the required hidden imports:

```bash
pyinstaller PCRemoteControl.spec
```

The executable is generated at `dist\PCRemoteControl.exe` (`dist/PCRemoteControl.app` on macOS). Packaging, the installer and CI are described in [../docs/PACKAGING.md](../docs/PACKAGING.md).

### Troubleshooting

#### If the "invalid syscall" error appears:

1. **Build in console mode to see the errors:**
   - Edit `PCRemoteControl.spec`
   - Change `console=False` to `console=True`
   - Rebuild: `pyinstaller PCRemoteControl.spec`
   - Run the .exe and read the messages

2. **Check that pywin32 is installed correctly:**
   ```bash
   python -c "import win32gui; print('OK')"
   ```

3. **Reinstall pywin32 with its post-install scripts:**
   ```bash
   pip uninstall pywin32
   pip install pywin32
   python -m pywin32_postinstall -install
   ```

#### Notes:

- The `.spec` file already includes the required hidden imports
- Unneeded libraries (numpy, pandas, etc.) are excluded to reduce the size
- The icon must be at `src\Logo.ico`
- Resources (images, icons) must live in the `src` folder
- **Recommendation:** always use the `.spec` file instead of the bare command

## Main Dependencies

- **Flask**: web framework
- **Flask-SocketIO**: real-time communication
- **CustomTkinter**: modern GUI
- **PyAutoGUI** and **pynput**: mouse and keyboard control
- **pycaw**: audio volume control
- **Pillow**: image processing
- **qrcode**: QR code generation
- **pystray**: system tray icon
- **zeroconf**: mDNS announcement on the local network

## Network Configuration

The server:
- Detects the local IP automatically
- Uses port **5723** by default
- Looks for a free port automatically if it is busy (then the app finds it again by name through mDNS)
- Listens on all interfaces (0.0.0.0)

- Announces itself with mDNS/Zeroconf (`_pcremote._tcp.local.`) so the app can find it by name

**Make sure that:**
- The Windows firewall allows the application inbound on private networks (the installer or `python main.py --configure-firewall` creates a program-based rule; it needs administrator rights)
- The PC and the mobile device are on the same local network

## Troubleshooting

### The server does not start
- Check that port 5723 is not in use
- Run as administrator if needed

### The mobile app cannot connect
- Check that both devices are on the same network (some routers block mDNS multicast between Wi-Fi clients; enter the IP manually then)
- Review the firewall configuration
- Make sure the IP shown is correct

### The server closes when the window is closed
- Enable "Minimizar a la bandeja" in the settings
- The server keeps running in the background

## Development

### Checks

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q        # about 1 minute: the contract tests start real servers
```

### Adding a new command

Follow the recipe in [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), section 8: document it in the protocol, add the domain type, write a handler registered in `pcremote/bootstrap.py`, add an adapter if a new OS capability is needed, and cover it with a unit test.

### Modifying the interface

The GUI lives in `pcremote/presentation/gui/`: `app.py` (window, sidebar, navigation), `views/` (home, settings, about), `theme.py`, `tray.py` and `qr_image.py`.

## Security Notes

- Clients must authenticate (PIN to pair, token afterwards) before any command runs
- Only a SHA-256 hash of each token is stored; a revoked device is disconnected and its token stops working
- The PIN is generated randomly, stored in `%APPDATA%/PCRemoteControl/server_pin.json` so saved devices keep working, and deleted when the application exits completely
- PIN and token attempts are rate limited per IP (5 failures, 60 s lock)
- The PIN is never served over HTTP
- The server is meant for the local network only
- Do not expose the server to the internet without additional security measures

---

**Developed by RISK KEEP**
