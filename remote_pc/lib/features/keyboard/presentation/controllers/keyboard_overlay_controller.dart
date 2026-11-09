import 'dart:async';
import 'dart:ui';

import 'package:flutter/foundation.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/protocol/protocol.dart';

/// State of the native-keyboard overlay: visibility, the draggable floating
/// button position and the window the server reported as active.
class KeyboardOverlayController extends ChangeNotifier {
  KeyboardOverlayController({
    required RemoteConnection connection,
    Duration deleteDelay = const Duration(milliseconds: 100),
  }) : _connection = connection,
       _deleteDelay = deleteDelay,
       _ready = connection.status == ConnectionStatus.ready {
    _hintSub = connection.keyboardHints.listen(_onHint);
    _statusSub = connection.statusStream.listen(_onStatus);
  }

  final RemoteConnection _connection;
  final Duration _deleteDelay;
  late final StreamSubscription<KeyboardHint> _hintSub;
  late final StreamSubscription<ConnectionStatus> _statusSub;

  bool _showNativeKeyboard = false;
  String? _currentWindow;

  /// Starts docked in the top-left corner, away from the scroll bar (right) and
  /// the click buttons (bottom), so it does not cover the touchpad. The user can
  /// still drag it anywhere.
  static const Offset defaultButtonPosition = Offset(4, 8);

  Offset _keyboardButtonPosition = defaultButtonPosition;
  bool _ready;
  bool _disposed = false;

  bool get showNativeKeyboard => _showNativeKeyboard;
  String? get currentWindow => _currentWindow;

  /// True while the connection is authenticated and commands can be sent.
  bool get isReady => _ready;

  Offset get keyboardButtonPosition => _keyboardButtonPosition;

  set keyboardButtonPosition(Offset position) {
    _keyboardButtonPosition = position;
    notifyListeners();
  }

  void toggle() {
    _showNativeKeyboard = !_showNativeKeyboard;
    notifyListeners();
  }

  void show() {
    _showNativeKeyboard = true;
    notifyListeners();
  }

  void hide() {
    _showNativeKeyboard = false;
    notifyListeners();
  }

  /// Selects all text in the focused field of the PC and deletes it.
  void deleteText() {
    _connection.fire(Commands.key('a', ctrl: true));
    Future<void>.delayed(_deleteDelay, () {
      if (_disposed) return;
      _connection.fire(Commands.key('backspace'));
    });
  }

  // The original app had the automatic "show" disabled on purpose: hints only
  // update the reported window name.
  void _onHint(KeyboardHint hint) {
    _currentWindow = hint.show ? hint.window : null;
    notifyListeners();
  }

  void _onStatus(ConnectionStatus status) {
    _ready = status == ConnectionStatus.ready;
    if (!_ready) _showNativeKeyboard = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _hintSub.cancel();
    _statusSub.cancel();
    super.dispose();
  }
}
