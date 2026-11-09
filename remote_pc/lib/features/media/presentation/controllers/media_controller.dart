import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';

/// Multimedia state and commands.
///
/// Volume and playback state come from the PC (`data` of the command
/// responses and `get_state` polling). Play/pause is applied optimistically
/// because the PC detects playback from its audio sessions, which lags behind
/// the key press; polled `playing` values are ignored for [playingHold] after
/// any press.
class MediaController extends ChangeNotifier {
  MediaController(
    this._sender, {
    DateTime Function() clock = DateTime.now,
    this.playingHold = const Duration(milliseconds: 2500),
    this.volumeSendInterval = const Duration(milliseconds: 60),
  }) : _clock = clock;

  final CommandSender _sender;
  final DateTime Function() _clock;
  final Duration playingHold;
  final Duration volumeSendInterval;

  double _volume = 0.5;
  bool _muted = false;
  bool _playing = false;
  bool _dragging = false;
  DateTime? _lastPress;
  DateTime? _lastVolumeSent;
  Timer? _volumeTimer;
  bool _disposed = false;

  /// 0.0 to 1.0. Keeps the last known value when the PC does not report one.
  double get volume => _volume;
  bool get muted => _muted;
  bool get playing => _playing;

  /// Asks the PC for its current state (used by the periodic poll).
  Future<void> refresh() async {
    final response = await _sender.request(
      Commands.media(MediaCommand.getState),
    );
    _apply(response.data);
  }

  Future<void> send(MediaCommand command) async {
    switch (command) {
      case MediaCommand.volumeUp:
      case MediaCommand.volumeDown:
      case MediaCommand.mute:
      case MediaCommand.next:
      case MediaCommand.previous:
      case MediaCommand.playPause:
        _lastPress = _clock();
        if (command == MediaCommand.playPause) {
          _playing = !_playing;
          _notify();
        }
        final response = await _sender.request(Commands.media(command));
        _apply(response.data);
      case MediaCommand.gameBar:
      case MediaCommand.record:
      case MediaCommand.micMute:
      case MediaCommand.setVolume:
      case MediaCommand.getState:
        _sender.fire(Commands.media(command));
    }
  }

  // ------------------------------------------------------------ slider

  /// Called on every slider change: updates the local value at once and sends
  /// `set_volume` at most every [volumeSendInterval].
  void volumeChanged(double value) {
    _dragging = true;
    _volume = value;
    _notify();
    final last = _lastVolumeSent;
    final now = _clock();
    if (last == null || now.difference(last) >= volumeSendInterval) {
      _sendVolume();
    } else {
      _volumeTimer ??= Timer(
        volumeSendInterval - now.difference(last),
        _sendVolume,
      );
    }
  }

  /// Called when the drag ends: always sends the final value.
  void volumeChangeEnd(double value) {
    _volume = value;
    _sendVolume();
    _dragging = false;
    _notify();
  }

  void _sendVolume() {
    _volumeTimer?.cancel();
    _volumeTimer = null;
    _lastVolumeSent = _clock();
    _sender.fire(Commands.media(MediaCommand.setVolume, level: _volume));
  }

  // ------------------------------------------------------------- state

  void _apply(Map<String, dynamic>? data) {
    if (data == null || _disposed) return;
    final volume = data['volume'];
    if (volume is num && !_dragging) {
      _volume = volume.toDouble().clamp(0.0, 1.0);
    }
    final muted = data['muted'];
    if (muted is bool) _muted = muted;
    final playing = data['playing'];
    final press = _lastPress;
    final settled = press == null || _clock().difference(press) >= playingHold;
    if (playing is bool && settled) _playing = playing;
    _notify();
  }

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _volumeTimer?.cancel();
    super.dispose();
  }
}
