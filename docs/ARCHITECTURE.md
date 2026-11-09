# Architecture and Design Patterns - PC Remote Control

Normative document. Every code change must respect it. If a rule gets in the way, discuss it and change this document first.

## 1. What the system is

Two applications that talk over Socket.IO on the local network:

- **Server (`Servidor/`)**: Python, Windows first with macOS and Linux supported through per-OS adapters. It exposes a Flask-SocketIO server, shows a QR and a PIN in a GUI (CustomTkinter, system tray), keeps running in the background and runs real actions on the PC (mouse, keyboard, media, power).
- **Mobile app (`remote_pc/`)**: Flutter. It scans the QR, pairs once with the PIN, then reconnects with a token (found automatically by mDNS) and sends commands.

It is a tool that **runs actions with full power over the PC**. Security and the separation between "receiving a command" and "executing it" are the main design criteria.

## 2. Architecture decision

### Server: layered architecture with Ports and Adapters ("light hexagonal")

Chosen because:

- The domain is small (commands, session, PIN, paired devices, settings). Full DDD or Clean Architecture with one use case per file would be over-engineering.
- What changes often are the **edges**: transport (Socket.IO), GUI, automation libraries (pyautogui/pynput/pycaw/win32). Ports isolate those edges and make the code testable without touching the real mouse.
- New commands can be added without editing a central `if/elif` (Open/Closed principle).

```
Servidor/
  main.py                          # entry point: calls bootstrap and runs the GUI
  pcremote/
    bootstrap.py                   # COMPOSITION ROOT: the only place that instantiates adapters and injects them
    domain/                        # Pure Python. FORBIDDEN imports: flask, socketio, pyautogui, pynput, win32*, customtkinter
      commands.py                  # command enums, validated payload dataclasses (MouseMove, KeyPress...), CommandResult
      errors.py                    # DomainError and subclasses, each with a stable wire code
      devices.py                   # PairedDevice (device_id, name, token_hash, created_at, last_seen)
      events.py                    # ServerStarted, ServerStopped, ClientAuthenticated, ClientDisconnected,
                                   #   ActiveWindowChanged, DevicePaired, DeviceRevoked
      ports.py                     # Protocols: MouseController, KeyboardController, MediaController, PowerController,
                                   #   DesktopController, PinStore, DeviceRepository, SettingsStore, NetworkInspector,
                                   #   AutoStartManager, FirewallManager, DiscoveryService, TransportServer,
                                   #   ActivityMonitor, EventPublisher
      session.py                   # ClientSession (id, ip, device_name, device_id, authenticated, connected_at)
      settings.py                  # AppSettings (server_id, minimize_to_tray, auto_start_server)
    application/                   # Orchestrates. Depends only on domain
      event_bus.py                 # EventPublisher implementation (subscribe/publish)
      session_registry.py          # replaces config.active_connections (thread-safe)
      auth_service.py              # PIN pairing (issues a token, stores its SHA-256 hash), token auth, per-IP rate limit
      device_service.py            # list and revoke paired devices (publishes DeviceRevoked)
      settings_service.py          # load/update persisted AppSettings, generates the persistent server_id
      command_dispatcher.py        # Registry: action name (and aliases) -> handler; validates the session
      server_controller.py         # start/stop use case: PIN, IP, free port, transport, activity monitor, discovery
      handlers/                    # one module per family: mouse.py, keyboard.py, media.py, system.py
    infrastructure/                # Concrete adapters of the ports
      paths.py                     # per-user data dir (%APPDATA%/PCRemoteControl) and resource paths
      platform/                    # per-OS assembly (Abstract Factory): the only place that chooses an OS
        __init__.py                # create_platform_adapters(app_name, startup_command, system=None) -> PlatformAdapters
        base.py                    # PlatformAdapters dataclass (power, desktop, media, autostart, firewall, monitor_factory)
        windows.py, macos.py, linux.py
      input/pyautogui_mouse.py, input/pynput_keyboard.py   # cross-platform input
      audio/pycaw_media.py         # Windows volume (pycaw imported lazily)
      power/windows_power.py       # Windows power and desktop actions
      persistence/file_pin_store.py, file_device_repository.py (devices.json), file_settings_store.py (settings.json)
      network/inspector.py         # local IP, host name and free-port checks
      network/zeroconf_discovery.py   # mDNS announcement of _pcremote._tcp.local. (zeroconf)
      os/_command.py               # run_command (shell=False, timeout, ExecutionError) and spawn_detached
      os/startup_registry.py       # Windows: HKCU Run key (command runs main.py --background)
      os/windows_firewall.py       # program-based netsh rule; relaunches elevated (runas) when needed
      os/noop_firewall.py          # macOS and Linux need no rule
      os/single_instance.py        # guard: only one server per user session (named mutex on Windows)
      os/_polling_watcher.py       # base class for active-window pollers
      os/window_watcher.py         # Windows active-window monitor (formerly input_detector.py)
      # macOS and Linux power, desktop, media, autostart (LaunchAgent, XDG) and window watchers
      # are in platform/macos.py and platform/linux.py
    presentation/
      transport/socketio_gateway.py   # the only module that knows Flask-SocketIO. Translates event -> auth/dispatcher -> response;
                                      #   disconnects sessions of revoked devices
      http/routes.py                  # /health and /status only; no secrets
      gui/                            # CustomTkinter
        theme.py, context.py, qr_image.py, tray.py, app.py
        views/home.py, views/settings.py (settings), views/devices.py (paired devices list),
        views/firewall_row.py (firewall status and "Configurar" button), views/about.py
  installer/                       # windows/PCRemoteControl.iss (Inno Setup), macos and linux notes
  tests/
    unit/ (domain, application, file stores, platform adapters with monkeypatched subprocess and tmp_path)
    contract/ (message format according to docs/PROTOCOL.md; starts real servers)
```

Dependency rule (inward only):

```
presentation  ->  application  ->  domain  <-  infrastructure
                       ^                            |
                       +------ implements ports ----+
```

`infrastructure` implements the ports defined in `domain/ports.py`; nothing in `domain` or `application` imports `infrastructure`. The only one that knows both sides is `bootstrap.py`.

### Mobile app: feature-first + light Clean + Provider

**Provider** is kept; changing the state manager would add no value here.

The app is the user's original hand-built app migrated into this structure. The UI (ConnectionScreen, ControlScreen with the Touchpad, Media, System and Settings tabs, the floating native-keyboard button) is preserved; migration was limited to pure extraction, rewiring and moving literals into strings files and identical-value color tokens. The old 460-line `WebSocketService` (hand-written Engine.IO framing over `web_socket_channel`, PIN validated through an HTTP endpoint, settings, keyboard state and vibration in one class) was replaced by `SocketIoConnection` + `ConnectionController` and the `BackgroundKeepAlive` abstraction.

```
remote_pc/lib/
  main.dart                 # portrait lock, background service init, runApp
  app/
    app.dart                # AppWrapper: ControlScreen when ready, ConnectionScreen otherwise
    providers.dart          # composition root: concrete connection, discovery, stores, background service
    theme.dart              # reproduces the original ThemeData (black scaffold, blue seed)
    app_colors.dart         # AppColors tokens, values identical to the colors the original UI used
  core/
    protocol/protocol.dart            # event names, error codes, Commands and AuthPayloads (mirror of docs/PROTOCOL.md)
    network/
      command_sender.dart             # CommandSender (isReady, fire, request) + CommandResponse: what the screens use
      remote_connection.dart          # RemoteConnection (extends CommandSender): pair, connectWithToken, status, keyboard hints
      socket_io_connection.dart       # socket_io_client implementation (websocket transport, FIFO request correlation)
      connection_status.dart          # idle, searching, connecting, authenticating, ready, reconnecting, error
      reconnect_policy.dart           # backoff 1, 2, 4, 8, 15 s, then 30 s cap
      discovery_service.dart, nsd_discovery_service.dart   # mDNS _pcremote._tcp via the nsd package
    storage/server_store.dart         # saved servers (shared_preferences) and tokens (flutter_secure_storage)
    background/                       # BackgroundKeepAlive + flutter_background_service implementation (Android foreground service)
    haptics/                          # HapticsService (HapticFeedback) + preference; replaces flutter_vibrate
    ui/ui_utils.dart
  features/
    connection/   data/legacy_connection_source.dart (one-time import of last_ip/last_pin), domain/{qr_payload,manual_input}.dart,
                  presentation/{controllers (ConnectionController),pages (connection_screen, qr_scanner_page),widgets,connection_strings.dart}
    control/      presentation/{control_screen.dart,control_strings.dart}    # tabs shell and status bar
    touchpad/     presentation/{controllers,widgets (touchpad_area, scroll_bar, click_buttons, options_panel),touchpad_screen.dart,touchpad_strings.dart}
    keyboard/     presentation/{controllers (keyboard_overlay_controller, hidden_text_bridge),widgets (floating_keyboard_button, ...),keyboard_strings.dart}
    media/        presentation/{controllers,media_screen.dart,media_strings.dart}
    system/       presentation/{controllers,system_screen.dart,system_strings.dart}
    settings/     data/settings_repository.dart, presentation/{controllers,settings_screen.dart,settings_strings.dart}
```

Compatibility with the original app data: the settings keys `sensitivity` (default 2.0) and `vibration` are preserved; `last_ip` and `last_pin` are imported once into the saved-servers store and deleted (the PIN is never stored; only the token is).

Each feature has only the layers it needs (`domain/` only when there is pure logic, `data/` only when it persists something).

Rules: screens talk to controllers (ChangeNotifier), and controllers talk to `CommandSender`; nothing in a screen imports the socket or the storage layer. Only the connection feature knows `RemoteConnection`, `DiscoveryService`, the stores and `BackgroundKeepAlive`. A file over about 300 lines is split by pure extraction. Dead code of the original app that no active screen references (`pages/remote.dart` mockup, `screens/tabs/*`, `screens/keyboard_screen.dart` and several empty files) was intentionally not migrated; it remains in the original copy.

Android build toolchain: Gradle wrapper 8.14.3, AGP 8.11.1, Kotlin 2.2.20 (Flutter 3.47 minimums). A machine-specific `org.gradle.java.home` must never be committed.

## 3. Mandatory design patterns

| Pattern | Where | Problem it solves |
|---|---|---|
| **Command + Registry (Dispatcher)** | `application/command_dispatcher.py`, `handlers/` | The `if/elif` in the old `handle_command` and the duplicated aliases (`media`/`media_control`, `press`/`down`/`up`) |
| **Ports and Adapters (Adapter)** | `domain/ports.py` + `infrastructure/` | The old handlers mixed logic and concrete libraries; impossible to test |
| **Composition Root / Dependency Injection** | `bootstrap.py` | Mutable global state in the old `config.py` (`PIN_CODE`, `SERVER_IP`, `active_connections`) |
| **Observer / simple event bus** | `application/event_bus.py` | Callbacks `on_auth_success`/`on_disconnect` passed by hand to the GUI; `DevicePaired`/`DeviceRevoked` refresh the GUI and drop revoked sessions |
| **Repository** | `PinStore`, `DeviceRepository`, `SettingsStore` | The old `utils.py` mixed PIN generation, files, network and ports |
| **Abstract Factory / Strategy** | `infrastructure/platform/` (`create_platform_adapters`), `PowerController`, `DesktopController`, `MediaController`, `AutoStartManager`, `FirewallManager`, `ActivityMonitor` | `platform.system()` branching inside each handler; one adapter family per OS |
| **Factory** | `bootstrap` factory functions | `create_app` / `create_socketio` scattered around |
| **Light MVC in the GUI** | `presentation/gui/views/` + `app.py` as presenter | The old 1000-line `gui_app.py` mixing logic, network and UI |
| **Provider + Repository (mobile)** | controllers/repositories per feature | Avoid `setState` with network logic in pages |
| **State (mobile)** | `ConnectionStatus` (idle, searching, connecting, authenticating, ready, reconnecting, error) | Connection states as loose booleans |
| **Strategy (mobile)** | `ReconnectPolicy` (backoff steps), `DiscoveryService` (nsd today) | Hardcoded delays and discovery inside the controller |

Introducing a pattern "just because" is forbidden. If a pattern does not solve a listed problem or a new documented one, it is not used.

## 4. Design rules

1. **One module, one responsibility.** A file over ~300 lines or a function over ~40 is a sign to split.
2. **No mutable global state.** No module variables such as `PIN_CODE`. State lives in injected objects.
3. **No `except Exception` that swallows errors.** Catch the concrete type; domain errors are translated at a single point (the gateway) to `{ok: false, code, message}`.
4. **No `print`.** Use `logging` with levels. Never log the PIN or the content of `text_input`.
5. **Validate every incoming payload** (types, ranges, enums) before running anything. The client is untrusted.
6. **Dangerous functions (shutdown, restart, logout, sleep)** require: an authenticated session, a dedicated handler and, in the app, explicit user confirmation.
7. **Subprocesses** go through `infrastructure/os/_command.run_command` (`shell=False`, timeout, failures wrapped in `ExecutionError`); never `os.system` with built text.
8. **OS-dependent code** lives only in `infrastructure/platform/` and the adapters it assembles. Windows-only libraries (`win32*`, `winreg`, `pycaw`, `comtypes`) are never imported at module level outside Windows adapters, so every module imports on every OS. A port capability is implemented for Windows, macOS and Linux or raises `UnsupportedActionError` with a clear message.
9. **Threads**: the server runs in its own thread; the GUI in the main thread. Every GUI update from another thread goes through `after(0, ...)`.
10. **Protocol compatibility**: changing an event or field requires updating `docs/PROTOCOL.md`, both sides, and bumping `protocol_version`.

## 5. Security (minimum threat model)

Threat: another device on the same network tries to control the PC.

- Access control has two stages. The **PIN** only pairs a new device. Pairing issues a random token (`secrets.token_urlsafe`) returned once; the server stores only its SHA-256 hash in `devices.json`, so a stolen file cannot be replayed. Later connections authenticate with the token. A device can be revoked at any time from the desktop app (its sessions are dropped). The PIN must be random (use `secrets`, not `random`), 6 digits minimum, and compared with `hmac.compare_digest`.
- **PIN lifecycle**: it is generated with `secrets` and persisted in the per-user data directory (`%APPDATA%/PCRemoteControl/server_pin.json`) so saved devices keep working while the application lives. It is **cleared when the application exits completely**, not when the server is stopped or started again. The file is never versioned.
- **Limit attempts**: maximum 5 failures per IP (PIN and token together), then a 60 s lock. Drop the client after the limit.
- No HTTP endpoint returns the PIN. `/health` and `/status` expose no secrets. The HTTP QR page was removed: the QR is shown only by the local GUI.
- Wildcard CORS is not allowed. The mobile client is not a browser and does not need it open.
- The PIN and any secret are **never versioned** (`server_pin.json` is in `.gitignore`). The Flask `SECRET_KEY` comes from an environment variable or is generated per run.
- Commands only after authentication; authentication is per connection (`sid`), not global.
- The QR contains `ip`, `port`, `code`, `id`, `name` and `v`. It is sensitive because of `code`: show it only in the local GUI.
- mDNS announces only the server id, host name and protocol version; it never exposes the PIN or a token.

## 6. Known technical debt (state as of 2026-11-08)

Suggested payment order. Each item must be closed in its own commit.

| # | Problem | File | Action | Status |
|---|---|---|---|---|
| 1 | `server_pin.json` versioned with a real PIN | `Servidor/server_pin.json` | `git rm --cached`, ignore, rotate PIN | Open: the user must untrack the file and rotate the PIN |
| 2 | `/status` and `/` publish the PIN without authentication | `routes.py` | remove the field | Resolved in the backend restructuring |
| 3 | CORS `*`, `logger=True`, `engineio_logger=True`, default `SECRET_KEY` | `config.py` | restrict, turn engine logs off, per-run secret | Resolved in the backend restructuring |
| 4 | No PIN attempt limit; PIN and auth data are printed | `socket_handlers.py` | `AuthService` with rate limit; `logging` without secrets | Resolved in the backend restructuring |
| 5 | `random` for the PIN | `utils.py` | `secrets.randbelow` | Resolved in the backend restructuring |
| 6 | `os.system` in shutdown/restart/etc. | `system_handler.py` | `subprocess.run` in `PowerController` | Resolved in the backend restructuring |
| 7 | `server.py` and `main.py` were dead/broken code (`from main import ...`, nonexistent `register_socket_handlers`); `main.py` used port 5000, the GUI 5723 | `server.py`, `main.py` | delete `server.py`; `main.py` becomes the real entry | Resolved in the backend restructuring |
| 8 | Global state in `config.py` | `config.py` | injected `SessionRegistry` + server config | Resolved in the backend restructuring |
| 9 | Dispatch `if/elif` and duplicated aliases | `socket_handlers.py` | `CommandDispatcher` | Resolved in the backend restructuring |
| 10 | 1000-line `gui_app.py`; `stop_server` did not really stop the server | `gui_app.py` | split into views; really stop the transport | Resolved in the backend restructuring |
| 11 | `media_handler.set_volume` with doubtful comments and nested `try` | `media_handler.py` | `PycawMedia` adapter | Resolved in the backend restructuring |
| 12 | The root `.gitignore` (generic Python template) hid Flutter files (`lib/`, `profile`, `Runner.xcworkspace`, `Icon?`, `*.manifest`), so the first GitHub push lacked the whole app | `.gitignore` | negation rules (applied); the user's original app migrated into `remote_pc/lib/` | Resolved: files are trackable; before pushing run `git status --ignored` and `git check-ignore -v` on new Flutter files |
| 13 | The original app used `web_socket_channel` with hand-written Engine.IO framing and validated the PIN over an HTTP endpoint | `pubspec.yaml`, `WebSocketService` | `socket_io_client` + `SocketIoConnection` and token pairing | Resolved (verified against a real server); `http`, `web_socket_channel` and `flutter_vibrate` removed |
| 14 | QR differs between GUI (JSON with code) and `/qr` (URL only) | `routes.py` / `gui_app.py` | single format in `docs/PROTOCOL.md` | Resolved in the backend restructuring |
| 15 | `input_detector` infers "text app" from the window title | `input_detector.py` | rename to `WindowWatcher`; configurable list | Resolved in the backend restructuring |
| 16 | `requirements.txt` outdated/duplicated (eventlet unused with `threading`) | `requirements.txt` | audit, pin versions, split `requirements-dev.txt` | Resolved in the backend restructuring |
| 17 | No tests | - | see section 7 | Partly resolved: server and app suites exist (section 11); coverage still to grow |
| 18 | `Servidor/src/Logo.ico` weighed 6 bytes (invalid file) | `src/Logo.ico` | regenerate the icon | Resolved: valid multi-size icon generated from `Logo.png` |
| 19 | `flask-socketio` 5.3.4 was incompatible with the installed `python-socketio` | `requirements.txt` | bump | Resolved: `flask-socketio>=5.5`, `python-socketio>=5.12` |
| 28 | Machine-specific `org.gradle.java.home` (path of another PC) and outdated Gradle/AGP/Kotlin broke `flutter build apk` | `remote_pc/android/` | remove the property; Gradle 8.14.3, AGP 8.11.1, Kotlin 2.2.20 | Resolved: debug APK builds |
| 29 | Junk build logs tracked in git | `remote_pc/android/build_*.txt` | `git rm` and ignore | Open |
| 30 | Original dead code not migrated: `pages/remote.dart`, `screens/tabs/*`, `screens/keyboard_screen.dart`, empty files | original app copy | none (kept only in the git-ignored original copy) | Intentional |
| 31 | `CommandSender.request()` matches responses FIFO (no request id in the protocol) | `docs/PROTOCOL.md`, `socket_io_connection.dart` | add a request id in a future protocol version | Open |
| 32 | `server_pin.json` with a real PIN is still in the old git history | git history | rotate the PIN; history rewrite (`git filter-repo` plus force push) needs the owner's confirmation | Open |
| 33 | Only `Logo.icns` and `Logo.ico` were regenerated; other platform icons are pending | `Servidor/src/`, `remote_pc/` | generate the remaining icons | Open |
| 20 | Windows firewall blocks inbound connections on a fresh PC | installer, `windows_firewall.py` | program-based rule | Automated by the installer and `--configure-firewall`; needs administrator rights; installer not built yet |
| 21 | `server_pin.json` is still in the git history | git history | clean the history, rotate the PIN | Open: the user must do it |
| 22 | PIN lifecycle: one PIN persisted until a full exit | `auth_service.py` | consider a short-lived pairing code shown only while pairing | Open (design decision) |
| 23 | No request id in the protocol: `request()` correlates responses FIFO | `PROTOCOL.md`, `socket_io_connection.dart` | add a `request_id` echoed in `command_response` in a future protocol version | Open |
| 24 | macOS and Linux adapters, installer and CI never ran on those systems | `infrastructure/platform/` | run CI, test on real machines | Open |
| 25 | `Logo.icns` missing for the macOS bundle | `Servidor/src/` | generate from `Logo.png` | Open |
| 26 | Wayland restricts input injection on Linux | `pynput`, `pyautogui` | X11 only for now; documented | Open (platform limit) |
| 27 | Binaries are unsigned (SmartScreen and Gatekeeper warnings) | packaging | code signing | Open |

## 7. Quality and tests

- **Server**: `pytest`. Unit tests of `domain` and `application` with fakes of the ports (without touching the real mouse). A contract test of each command message. `ruff` for linting and formatting; `mypy` on `domain` and `application`. Install the tools with `pip install -r requirements-dev.txt`, then run `ruff check .` and `pytest`.
- **Platform adapters**: tests monkeypatch `subprocess.run`/`run_command` and use `tmp_path` for generated files; they never execute real system commands or touch the real firewall, registry or autostart. CI runs on Windows, macOS and Linux.
- **App**: `flutter analyze` without issues and `flutter test` green. Feature tests use `FakeCommandSender`; connection tests use fakes of `RemoteConnection`, `DiscoveryService` and `ServerStore`.
- The server suite takes about 1 minute because the contract tests start and stop real servers.
- A new feature without a test of its handler/controller is not considered finished.

## 8. How to add a new command (recipe)

1. Define the name and payload in `docs/PROTOCOL.md`.
2. Server: add the enum value and the payload dataclass in `domain/commands.py`; if it needs a new OS capability, extend the port in `domain/ports.py`.
3. Implement the adapter for Windows, macOS and Linux in `infrastructure/` (or raise `UnsupportedActionError` for the OS that cannot do it); if it is a new capability, add it to the `PlatformAdapters` bundle.
4. Write the handler in `application/handlers/` and register it in `bootstrap.py`.
5. Unit test with a fake of the port.
6. App: add the builder in `core/protocol/protocol.dart`, the controller method in the feature and the UI (Spanish text in the feature strings file).
7. Bump `protocol_version` if it breaks compatibility.

## 9. Background lifecycle and multi-OS roadmap

### Background behavior

- `python main.py --background` starts hidden in the system tray. Closing the window hides it (instead of exiting) when "Minimizar a la bandeja" is on. The server keeps running with the window closed; only "Salir" in the tray menu stops everything.
- Settings (`minimize_to_tray`, `auto_start_server`, `server_id`) persist in `%APPDATA%/PCRemoteControl/settings.json`; paired devices in `devices.json`; the PIN in `server_pin.json` (cleared on a full exit).
- A single-instance guard prevents two servers from fighting for the port.
- The autostart entry launches the app with `--background`.
- Per-OS startup:
  - **Windows**: per-user logon autostart (Run key or a Scheduled Task). Do **not** run it as a Windows Service: services live in session 0 and cannot inject mouse or keyboard input into the user desktop.
  - **macOS**: a LaunchAgent (plus the Accessibility permission for input control).
  - **Linux**: `systemd --user` or XDG autostart (X11; Wayland restricts input injection).
- **Firewall**: Windows blocks inbound connections until a rule exists. The rule is program-based (the executable, private and domain profiles, any protocol, so it also covers mDNS and any fallback port) and needs administrator rights. It is created by the Inno Setup installer, or on demand with `main.py --configure-firewall` (removed with `--remove-firewall`); the settings view shows its status and a "Configurar" button that relaunches elevated. macOS and Linux use a no-op adapter. Tests never touch the real firewall.

### Multi-OS roadmap

1. **Done (untested on real macOS and Linux)**: adapters per OS behind the existing ports (`PowerController`, `DesktopController`, `MediaController`, `AutoStartManager`, `FirewallManager`, `ActivityMonitor`), selected by `create_platform_adapters` in `bootstrap.py` with `platform.system()`. Domain and application did not change.
2. **Done in code**: tray differences per OS (`run_detached` on macOS, minimize instead of hide when no tray backend exists on Linux). Permissions (macOS Accessibility and Automation) are documented, not detected.
3. Later, split a **headless core** (server, pairing, adapters) from the UI so the UI becomes a thin client of the core (candidate: Flutter Desktop). The layering already allows it because the GUI only talks to application services and the event bus.
4. Build and package per OS (PyInstaller does not cross-compile): `PCRemoteControl.spec` is platform-aware, the Windows installer exists (`installer/windows/PCRemoteControl.iss`), macOS and Linux have notes only, and the CI matrix builds on all three. See `docs/PACKAGING.md`.

## 10. Migration status

- **Backend (`Servidor/`)**: restructured into the `pcremote/` package following this document. Entry point: `python main.py`. The legacy files (`gui_app.py`, `server.py`, `config.py`, `routes.py`, `socket_handlers.py`, `utils.py`, `input_detector.py` and the old `*_handler.py` modules) are removed.
- **Pairing, discovery and background mode**: implemented on the server (token pairing with revocation, mDNS announcement, persisted settings, `--background`, single-instance guard) and on the app (token storage, mDNS rediscovery, reconnection with backoff).
- **Multi-OS**: per-OS adapter bundles exist for Windows, macOS and Linux; only Windows has been exercised on a real machine.
- **Flutter app (`remote_pc/lib/`)**: the user's original hand-built app was migrated into the structure of section 2 with the UI preserved. `WebSocketService` was replaced by `SocketIoConnection` + `ConnectionController` and `BackgroundKeepAlive`; the touchpad screen (1088 lines) was split by pure extraction; the original `sensitivity` and `vibration` settings and the one-time `last_ip`/`last_pin` import keep existing installs working. A copy of the original app stays in the git-ignored folder `Nueva carpeta/`, which must never be committed.
- **Packaging**: platform-aware PyInstaller spec, Windows Inno Setup script, macOS and Linux notes and a CI workflow exist but have not run yet.

## 11. Verification status

Tested:
- Server: `ruff check .` clean and 87 tests passing (`pytest -q`): unit tests of domain, application, file stores and platform adapters (mocked subprocess), plus contract tests against a real Socket.IO server (pairing, token reconnect, revocation, rate limiting, `keyboard_event`, `/status` without PIN).
- Flutter: `flutter analyze` clean and 78 tests passing (1 live test skipped unless `PCREMOTE_HOST`, `PCREMOTE_PORT` and `PCREMOTE_PIN` are set): protocol builders, QR payload, reconnect policy, connection controller with fakes, legacy `last_ip`/`last_pin` import, widget smoke tests of the migrated screens, keyboard overlay, media, system confirmation, settings persistence with the original keys. `flutter build apk --debug` succeeds.
- End to end against a real running server: the Dart client paired with a PIN, was rejected with `INVALID_PIN`, sent commands, reconnected with the token and was rejected with `INVALID_TOKEN` for a bad one. A Python client verified pairing, token reconnect, revocation and port release on stop.
- mDNS announcement and discovery roundtrip on the development machine (Python side).

Not verified:
- The Flutter app on a real device or emulator: real-device visuals and gestures (the migration is verified by identical constants and structural widget tests, not by pixels), haptics, layout, the Android 14 foreground-service notification, iOS permissions and the iOS build.
- mDNS discovery through `nsd` on a real network and on iOS (Bonjour and local network permission), and on networks that block multicast.
- Camera QR scanning with `mobile_scanner`.
- The macOS and Linux adapters (osascript, pmset, systemctl, loginctl, playerctl, pactl, xdotool, LaunchAgent, XDG autostart, tray backends, Wayland).
- The Windows UAC elevation path and real `netsh` rule creation, the real tray, autostart at logon, and the single-instance guard on other OSes.
- The PyInstaller builds, the Inno Setup installer and the first CI run.
