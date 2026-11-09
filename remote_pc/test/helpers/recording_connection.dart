import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/remote_connection.dart';

/// Connection double that records every command and lets tests push
/// status changes and keyboard hints.
class RecordingConnection implements RemoteConnection {
  RecordingConnection({
    ConnectionStatus status = ConnectionStatus.ready,
    this.onRequest,
  }) : _status = status;

  /// Builds the response of a request; defaults to a bare success.
  CommandResponse Function(Map<String, dynamic> payload)? onRequest;

  final fired = <Map<String, dynamic>>[];
  final requested = <Map<String, dynamic>>[];
  final _statusController = StreamController<ConnectionStatus>.broadcast();
  final _hintController = StreamController<KeyboardHint>.broadcast();
  final _failureController = StreamController<ConnectionFailure>.broadcast();
  ConnectionStatus _status;

  @override
  ConnectionStatus get status => _status;

  @override
  Stream<ConnectionStatus> get statusStream => _statusController.stream;

  @override
  Stream<KeyboardHint> get keyboardHints => _hintController.stream;

  @override
  Stream<ConnectionFailure> get failures => _failureController.stream;

  @override
  bool get isReady => _status == ConnectionStatus.ready;

  void emitStatus(ConnectionStatus value) {
    _status = value;
    _statusController.add(value);
  }

  void emitHint(KeyboardHint hint) => _hintController.add(hint);

  @override
  void fire(Map<String, dynamic> payload) {
    if (isReady) fired.add(payload);
  }

  @override
  Future<CommandResponse> request(Map<String, dynamic> payload) async {
    if (!isReady) return CommandResponse.notReady;
    requested.add(payload);
    return onRequest?.call(payload) ?? const CommandResponse(ok: true);
  }

  @override
  Future<PairingOutcome> pair(
    ServerEndpoint endpoint,
    String pin,
    String deviceName,
  ) {
    throw UnimplementedError();
  }

  @override
  Future<void> connectWithToken(ServerEndpoint endpoint, String token) {
    throw UnimplementedError();
  }

  @override
  Future<void> disconnect() async => emitStatus(ConnectionStatus.idle);

  Future<void> close() async {
    await _statusController.close();
    await _hintController.close();
    await _failureController.close();
  }
}

/// Intercepts haptic calls on the platform channel and returns the types
/// that were requested.
List<String> mockHaptics(TestDefaultBinaryMessenger messenger) {
  final calls = <String>[];
  messenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
    if (call.method == 'HapticFeedback.vibrate') {
      calls.add(call.arguments as String);
    }
    return null;
  });
  return calls;
}
