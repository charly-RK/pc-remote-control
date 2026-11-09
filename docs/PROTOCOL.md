# Socket.IO Protocol - PC Remote Control

Single source of truth for the contract between the server and the mobile app. Current `protocol_version`: **1**.

> Status: this document describes the restructured server and the Flutter client in `remote_pc/lib/`. Items marked **[CHANGED]** differ from the legacy server and are kept compatible where noted. The Dart client was verified against a real running server (pairing, token reconnect, rejected PIN and token, commands); it has not been run on a real device yet.

## 1. Connection and QR

- Transport: Socket.IO over HTTP on the local network. Default port `5723` (another free port is used if it is busy).
- QR content (canonical format, JSON):

```json
{ "ip": "192.168.1.20", "port": 5723, "code": "123456", "id": "9f2c4e1a7b3d4c0e8a5b6d7e8f901234", "name": "OFFICE-PC", "v": 1 }
```

`id` is the persistent server id (generated once and stored in `settings.json`), `name` is the host name and `v` the protocol version. `id` and `name` are additive fields: clients that only read `ip`, `port` and `code` keep working.

- **[CHANGED]** The HTTP QR page was removed. The QR is shown only by the desktop GUI, which uses this JSON format.
- The server also exposes `/health` and `/status` over HTTP. Neither returns the PIN.

## 2. Discovery (mDNS/Zeroconf)

The server announces itself on the local network while it is running, so a client can find it even if the IP address or the port changed.

- Service type: `_pcremote._tcp.local.`
- Instance name: `<hostname> (<id6>)`, where `<id6>` is the first six characters of the server id.
- Port: the Socket.IO port in use.
- TXT records: `id` (persistent server id), `name` (host name), `v` (protocol version).

Clients resolve the service by `id`, never by IP. A manual `ip:port` remains available as a fallback for networks that block multicast. Discovery is a convenience: if it fails to start, the server keeps running and the QR and manual entry still work.

## 3. Lifecycle

1. Client connects -> the server creates a session with `authenticated=false`.
2. Client emits `authenticate` with a PIN (first time, pairing) or a token (already paired).
3. Server answers with `authentication_result`.
4. If `success`, the server emits `system_info`. From then on the client may emit `command`.
5. Any `command` before authentication answers `command_response` with `ok=false`.
6. After 5 failed attempts (PIN or token) from an IP, that IP is locked for 60 seconds and its connections are refused or dropped.
7. If the device is revoked from the desktop app, the server disconnects it and its token stops working.

### Pairing flow

```
First connection        client --authenticate {pin, device_name}--> server
                        client <--authentication_result {success, message, token, device_id}-- server
                        (the client stores token + device_id + server id)

Later connections       client --authenticate {token}--> server
                        client <--authentication_result {success, message, device_id}-- server
```

- The `token` is returned **only once**, in the pairing response. The server stores only its SHA-256 hash, so a lost token cannot be recovered: the device must be paired again with the PIN.
- Legacy clients that send the PIN on every connection keep working: they simply pair a new device each time and may ignore the `token`. Because the new fields are additive, `protocol_version` stays **1**.
- Revoking a device (desktop app, "paired devices" list) deletes its hash. The next `authenticate {token}` fails with `INVALID_TOKEN`.

## 4. Client -> server events

### `authenticate`
Pairing with the PIN:
```json
{ "pin": "123456", "device_name": "Pixel 8" }
```
Reconnecting with a token:
```json
{ "token": "<token received when pairing>" }
```
If `token` is present it takes precedence over `pin`. (The server also accepts the same object serialized as a JSON string.)

### `command`
All commands carry `action`. The answer always arrives as `command_response`.

**Limitation (protocol version 1): no request id.** `command_response` does not say which command it answers, only `original_action` on failures. The Flutter client therefore pairs each response with its oldest pending `request()` (FIFO). That is correct only while every request receives exactly one response and responses keep the order of the requests, which holds for a single socket handled sequentially. High-frequency input such as `mouse_move` is sent with `fire()`; since the additive `noack` flag (see below) the server does not answer those commands at all, so they can no longer be confused with a pending `request()`. Recommendation for a future protocol version: let the client send a `request_id` in the command and have the server echo it in `command_response`; it is an additive field, so older clients keep working.

| `action` | Fields | Notes |
|---|---|---|
| `mouse_move` | `x:int`, `y:int` | relative displacement in pixels |
| `mouse_click` | `button: left\|right\|middle`, `type: single\|double\|down\|up` | |
| `mouse_scroll` | `dx:int`, `dy:int` | |
| `key_press` | `key:str`, `ctrl`, `alt`, `shift`, `win` (bool) | with modifiers it is sent as a hotkey |
| `text_input` | `text:str` | never written to logs |
| `media_control` | `command: play_pause\|next\|previous\|volume_up\|volume_down\|mute\|set_volume\|get_state\|game_bar\|record\|mic_mute`, `level:float 0..1` (only `set_volume`) | Every media command answers with the resulting audio state in `data` (see `command_response`). `get_state` only reads it. |
| `system_control` | `command: shutdown\|restart\|sleep\|logout\|lock\|task_manager\|explorer\|capture\|show_desktop\|open_browser` | `shutdown`, `restart`, `sleep` and `logout` require confirmation in the app |

Legacy aliases accepted for compatibility with the current app: `press`/`down`/`up` as the `action` of a key command (they select the key state; `key_press` means a plain press), `media` for `media_control`, and `system`/`screen` for `system_control`. The dispatcher normalizes them; the new app uses only the canonical names in the table.

**[CHANGED]** An unknown `media_control` `command` now answers `UNKNOWN_COMMAND`/`INVALID_PAYLOAD` instead of being forwarded as a key press. Every payload is validated (types, ranges, enums) before any action runs.

## 5. Server -> client events

### `authentication_result`
Pairing success (the only response that carries `token`):
```json
{ "success": true, "message": "Authenticated successfully", "token": "...", "device_id": "9f2c4e1a..." }
```
Token success:
```json
{ "success": true, "message": "Authenticated successfully", "device_id": "9f2c4e1a..." }
```
Failure:
```json
{ "success": false, "message": "Invalid token", "code": "INVALID_TOKEN" }
```
Failure codes: `INVALID_PIN`, `INVALID_TOKEN`, `RATE_LIMITED`, `INVALID_PAYLOAD` (for example, neither `pin` nor `token` was sent). `message` is technical English text; the app composes the user-facing Spanish text from `code`.

### `system_info`
```json
{ "platform": "Windows", "platform_version": "10.0.26200", "machine": "AMD64", "protocol_version": 1 }
```

### `command_response`
```json
{ "ok": true, "message": "..." }
{ "ok": true, "message": "Media command: volume_up", "data": { "volume": 0.52, "muted": false, "playing": true } }
{ "ok": false, "code": "NOT_AUTHENTICATED", "error": "Not authenticated", "original_action": "mouse_move" }
```
`data` is optional and only present when the command returns information. Media commands (`volume_up`, `volume_down`, `mute`, `set_volume`, `play_pause`, `next`, `previous`, `get_state`) return `{ "volume": float 0..1 | null, "muted": bool | null, "playing": bool | null }` read after the action (key based commands wait about 40 ms so the OS has applied them). A field is `null` when it cannot be read on that platform; failing to read the state never fails the command. `playing` is a heuristic: on Windows it is true when some application other than the system sounds and this server renders audio (an active audio session), so it can lag a moment behind a play/pause and does not tell which app is playing. It is `null` on macOS and Linux. Clients should apply the state they receive but ignore a `playing` value for ~2 s after sending play/pause themselves.

#### `noack` (fire-and-forget commands)
A `command` payload may carry `"noack": true`. The server executes it and sends **no** `command_response`, not even on error (the failure is only logged at debug level). Use it for high-frequency input such as `mouse_move` and `mouse_scroll`: it halves the traffic and keeps responses aligned with the client's FIFO `request()` matching. Without the flag the server always answers, as before. The server also disables Nagle's algorithm (`TCP_NODELAY`) on accepted sockets so small frames are not delayed.

Failures always include a stable `code` (for the app logic) plus `error` as technical text. Codes: `NOT_AUTHENTICATED`, `INVALID_PAYLOAD`, `UNKNOWN_COMMAND`, `UNSUPPORTED`, `EXECUTION_FAILED`.

### `keyboard_event`
```json
{ "event": "show|hide", "data": { "window": "window title", "timestamp": 1730000000.0 } }
```
Sent only to authenticated clients when the active window changes. It hints whether the app should show the keyboard. The Flutter client exposes it as `RemoteConnection.keyboardHints`; the control shell only suggests switching to the keyboard tab, it never switches by itself.

## 6. Client reconnection guidance (mobile app)

Not part of the wire contract, but the server is designed for it and the Flutter client (`ConnectionController`, `ReconnectPolicy`, `NsdDiscoveryService`) implements it:

- Use an explicit connection state: `searching`, `connecting`, `authenticating`, `ready`, `reconnecting`, `error`.
- Heartbeat: the Socket.IO ping already runs every 25 s (timeout 60 s); the client treats a disconnect or connect error as a lost connection.
- Reconnect with exponential backoff: 1 s, 2 s, 4 s, 8 s, 15 s, then capped at 30 s (deterministic, reset after a successful connection).
- On every attempt: try the **saved token first** against the last known `ip:port`; if that fails, **rediscover by server id** through mDNS and retry with the new address; fall back to the last known `ip:port`. Servers added by hand have a synthetic id (`manual:ip:port`) until they are found by mDNS, so they cannot be rediscovered if the IP changes.
- `INVALID_TOKEN` means the device was revoked or the server data was reset: delete the saved token and ask for the PIN again. `RATE_LIMITED`: wait before retrying.
- iOS cannot keep the socket alive in the background: the client reconnects when the app returns to the foreground. Android may use a foreground service when background control is wanted (not implemented).

## 7. Contract rules

- A new optional field does not break compatibility. Renaming, removing or changing the type of a field does.
- Every breaking change bumps `protocol_version`; the server reports it in `system_info` and the app warns when it does not match.
- Text that the end user sees (for example the wrong PIN notice) is composed by the app in Spanish from the `code`; the server returns technical English text.
- The PIN lives in the per-user data directory (`%APPDATA%/PCRemoteControl/server_pin.json`) and is cleared when the application exits completely. It is only needed to pair a device; after pairing, the token is used. A client that saved the PIN must handle `INVALID_PIN` by asking for the new one.
- Paired devices are stored (token hashes only) in `devices.json` in the same directory.
