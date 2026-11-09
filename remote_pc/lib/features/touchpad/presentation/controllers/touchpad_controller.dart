import 'dart:async';
import 'dart:ui';

import 'package:flutter/foundation.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';

/// Touchpad input logic: smooth cursor movement, scroll bar, continuous
/// scrolling and the click buttons. Behaviour (thresholds, throttling and
/// timings) matches the original hand-built screen.
class TouchpadController extends ChangeNotifier {
  TouchpadController({
    required CommandSender sender,
    required SettingsController settings,
    required HapticsService haptics,
    DateTime Function() clock = DateTime.now,
  }) : _sender = sender,
       _settings = settings,
       _haptics = haptics,
       _clock = clock {
    _lastSent = _clock();
    _lastScrollSent = _clock();
  }

  /// Minimum time between cursor/scroll updates: one per frame at 60 Hz.
  /// (The original >32 ms rule sent about 20 updates per second and felt choppy.)
  static const int throttleMs = 16;
  static const double scrollBarMultiplier = 2;
  static const Duration continuousScrollInterval = Duration(milliseconds: 100);
  static const int firstScrollStep = 100;
  static const int repeatScrollStep = 50;

  final CommandSender _sender;
  final SettingsController _settings;
  final HapticsService _haptics;
  final DateTime Function() _clock;

  Offset? _lastTouch;
  double _accX = 0;
  double _accY = 0;
  late DateTime _lastSent;

  double _accScrollY = 0;
  late DateTime _lastScrollSent;

  bool _isDragging = false;
  bool _scrollDragging = false;
  bool _isScrollingUp = false;
  Timer? _continuousScrollTimer;

  bool get isDragging => _isDragging;
  bool get scrollDragging => _scrollDragging;
  bool get isScrollingUp => _isScrollingUp;
  bool get continuousScrolling => _continuousScrollTimer != null;

  // ----------------------------------------------------------- cursor

  void panStart(Offset position) {
    _lastTouch = position;
    _accX = 0;
    _accY = 0;
    _isDragging = true;
    notifyListeners();
  }

  void panUpdate(Offset position) {
    final last = _lastTouch;
    if (last == null) return;
    final sensitivity = _settings.sensitivity;
    _accX += (position.dx - last.dx) * sensitivity;
    _accY += (position.dy - last.dy) * sensitivity;

    // Coalesce to at most one update per frame (60 per second).
    final now = _clock();
    if (now.difference(_lastSent).inMilliseconds >= throttleMs) {
      final moveX = _accX.truncate();
      final moveY = _accY.truncate();
      if (moveX != 0 || moveY != 0) {
        _sender.fire(Commands.mouseMove(moveX, moveY));
        _accX -= moveX;
        _accY -= moveY;
        _lastSent = now;
      }
    }
    _lastTouch = position;
  }

  void panEnd() {
    _isDragging = false;
    _lastTouch = null;
    notifyListeners();
  }

  // ----------------------------------------------------------- scroll

  void scrollBarStart() {
    _accScrollY = 0;
    _scrollDragging = true;
    notifyListeners();
  }

  void scrollBarUpdate(double deltaY) {
    _accScrollY += deltaY * scrollBarMultiplier;
    final now = _clock();
    if (now.difference(_lastScrollSent).inMilliseconds >= throttleMs) {
      final scrollY = _accScrollY.truncate();
      if (scrollY != 0) {
        _sender.fire(Commands.mouseScroll(dy: scrollY));
        _accScrollY -= scrollY;
        _lastScrollSent = now;
      }
    }
  }

  void scrollBarEnd() {
    _scrollDragging = false;
    notifyListeners();
  }

  void startContinuousScroll({required bool up}) {
    _isScrollingUp = up;
    _continuousScrollTimer?.cancel();
    _sender.fire(
      Commands.mouseScroll(dy: up ? firstScrollStep : -firstScrollStep),
    );
    _haptics.selection();
    _continuousScrollTimer = Timer.periodic(continuousScrollInterval, (_) {
      _sender.fire(
        Commands.mouseScroll(
          dy: _isScrollingUp ? repeatScrollStep : -repeatScrollStep,
        ),
      );
    });
    notifyListeners();
  }

  void stopContinuousScroll() {
    _continuousScrollTimer?.cancel();
    _continuousScrollTimer = null;
    notifyListeners();
  }

  // ----------------------------------------------------------- clicks

  void leftClick() {
    _sender.fire(Commands.mouseClick(MouseButton.left, ClickType.single));
    _haptics.light();
  }

  void doubleClick() {
    _sender.fire(Commands.mouseClick(MouseButton.left, ClickType.double));
    _haptics.medium();
  }

  void middleClick() {
    _sender.fire(Commands.mouseClick(MouseButton.middle, ClickType.single));
    _haptics.light();
  }

  void rightClick() {
    _sender.fire(Commands.mouseClick(MouseButton.right, ClickType.single));
    _haptics.light();
  }

  // -------------------------------------------------------- shortcuts

  void shortcut(String key, {bool ctrl = false}) {
    _sender.fire(Commands.key(key, ctrl: ctrl));
    _haptics.light();
  }

  void quickKey(String key) => shortcut(key);

  @override
  void dispose() {
    _continuousScrollTimer?.cancel();
    super.dispose();
  }
}
