/// Wire contract with the server. Mirrors docs/PROTOCOL.md (protocol version 1).
/// Event names and payload builders live ONLY here.
library;

const int protocolVersion = 1;

/// Port the desktop server uses by default (it may pick another if busy).
const int defaultServerPort = 5723;

class ProtocolEvents {
  static const authenticate = 'authenticate';
  static const authenticationResult = 'authentication_result';
  static const command = 'command';
  static const commandResponse = 'command_response';
  static const systemInfo = 'system_info';
  static const keyboardEvent = 'keyboard_event';
}

class ErrorCodes {
  static const notAuthenticated = 'NOT_AUTHENTICATED';
  static const invalidPin = 'INVALID_PIN';
  static const invalidToken = 'INVALID_TOKEN';
  static const rateLimited = 'RATE_LIMITED';
  static const invalidPayload = 'INVALID_PAYLOAD';
  static const unknownCommand = 'UNKNOWN_COMMAND';
  static const unsupported = 'UNSUPPORTED';
  static const executionFailed = 'EXECUTION_FAILED';
}

enum MouseButton { left, right, middle }

enum ClickType { single, double, down, up }

enum KeyState { press, down, up }

enum MediaCommand {
  playPause('play_pause'),
  next('next'),
  previous('previous'),
  volumeUp('volume_up'),
  volumeDown('volume_down'),
  mute('mute'),
  setVolume('set_volume'),
  gameBar('game_bar'),
  record('record'),
  micMute('mic_mute'),
  getState('get_state');

  const MediaCommand(this.wire);
  final String wire;
}

enum SystemCommand {
  shutdown('shutdown'),
  restart('restart'),
  sleep('sleep'),
  logout('logout'),
  lock('lock'),
  taskManager('task_manager'),
  explorer('explorer'),
  capture('capture'),
  showDesktop('show_desktop'),
  openBrowser('open_browser');

  const SystemCommand(this.wire);
  final String wire;

  /// Commands that must be confirmed by the user before sending.
  bool get isDestructive =>
      this == shutdown || this == restart || this == sleep || this == logout;
}

/// Payload builders for the `command` event.
class Commands {
  static Map<String, dynamic> mouseMove(int x, int y) => {
    'action': 'mouse_move',
    'x': x,
    'y': y,
  };

  static Map<String, dynamic> mouseClick(MouseButton button, ClickType type) =>
      {'action': 'mouse_click', 'button': button.name, 'type': type.name};

  static Map<String, dynamic> mouseScroll({int dx = 0, required int dy}) => {
    'action': 'mouse_scroll',
    'dx': dx,
    'dy': dy,
  };

  static Map<String, dynamic> key(
    String key, {
    KeyState state = KeyState.press,
    bool ctrl = false,
    bool alt = false,
    bool shift = false,
    bool win = false,
  }) => {
    'action': state == KeyState.press ? 'key_press' : state.name,
    'key': key,
    if (ctrl) 'ctrl': true,
    if (alt) 'alt': true,
    if (shift) 'shift': true,
    if (win) 'win': true,
  };

  static Map<String, dynamic> text(String text) => {
    'action': 'text_input',
    'text': text,
  };

  static Map<String, dynamic> media(MediaCommand command, {double? level}) => {
    'action': 'media_control',
    'command': command.wire,
    if (command == MediaCommand.setVolume && level != null) 'level': level,
  };

  static Map<String, dynamic> system(SystemCommand command) => {
    'action': 'system_control',
    'command': command.wire,
  };
}

/// Authentication payloads.
class AuthPayloads {
  static Map<String, dynamic> pair(String pin, String deviceName) => {
    'pin': pin,
    'device_name': deviceName,
  };

  static Map<String, dynamic> token(String token) => {'token': token};
}
