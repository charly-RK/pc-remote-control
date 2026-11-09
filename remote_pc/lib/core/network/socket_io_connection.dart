import 'dart:async';
import 'dart:collection';

import 'package:flutter/foundation.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:socket_io_client/socket_io_client.dart' as io;

/// Socket.IO implementation of [RemoteConnection].
///
/// Protocol note: the `command_response` event carries no request id, so
/// [request] resolves with the next response received, in FIFO order. This is
/// correct as long as every `request` produces exactly one response.
/// Responses to [fire] calls are discarded when no request is pending.
class SocketIoConnection implements RemoteConnection {
  SocketIoConnection({
    this.connectTimeout = const Duration(seconds: 6),
    this.requestTimeout = const Duration(seconds: 5),
  });

  final Duration connectTimeout;
  final Duration requestTimeout;

  final _statusController = StreamController<ConnectionStatus>.broadcast();
  final _hintController = StreamController<KeyboardHint>.broadcast();
  final _failureController = StreamController<ConnectionFailure>.broadcast();
  final Queue<Completer<CommandResponse>> _pending = Queue();

  io.Socket? _socket;
  ConnectionStatus _status = ConnectionStatus.idle;
  bool _closing = false;

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

  void _setStatus(ConnectionStatus value) {
    if (_status == value) return;
    _status = value;
    _statusController.add(value);
  }

  @override
  Future<PairingOutcome> pair(
    ServerEndpoint endpoint,
    String pin,
    String deviceName,
  ) async {
    final result = await _connectAndAuthenticate(
      endpoint,
      AuthPayloads.pair(pin, deviceName),
    );
    final token = result['token'];
    final deviceId = result['device_id'];
    if (token is! String || deviceId is! String) {
      await _teardown();
      _setStatus(ConnectionStatus.error);
      throw const ConnectionFailure(
        ErrorCodes.executionFailed,
        'Pairing response is missing the token',
      );
    }
    return PairingOutcome(token: token, deviceId: deviceId);
  }

  @override
  Future<void> connectWithToken(ServerEndpoint endpoint, String token) async {
    await _connectAndAuthenticate(endpoint, AuthPayloads.token(token));
  }

  Future<Map<String, dynamic>> _connectAndAuthenticate(
    ServerEndpoint endpoint,
    Map<String, dynamic> authPayload,
  ) async {
    await _teardown();
    _closing = false;
    _setStatus(ConnectionStatus.connecting);

    final socket = io.io(
      endpoint.url,
      io.OptionBuilder()
          .setTransports(['websocket'])
          .disableAutoConnect()
          .disableReconnection()
          .enableForceNew()
          .build(),
    );
    _socket = socket;

    final connected = Completer<void>();
    final authResult = Completer<Map<String, dynamic>>();

    socket.onConnect((_) {
      if (!connected.isCompleted) connected.complete();
    });
    socket.onConnectError((error) {
      if (!connected.isCompleted) {
        connected.completeError(
          const ConnectionFailure(ConnectionFailure.network),
        );
      }
    });
    socket.on(ProtocolEvents.authenticationResult, (data) {
      if (!authResult.isCompleted) authResult.complete(_asMap(data));
    });
    socket.on(ProtocolEvents.commandResponse, _onCommandResponse);
    socket.on(ProtocolEvents.keyboardEvent, _onKeyboardEvent);
    socket.onDisconnect((_) => _onDisconnected());

    try {
      socket.connect();
      await connected.future.timeout(
        connectTimeout,
        onTimeout: () =>
            throw const ConnectionFailure(ConnectionFailure.timeout),
      );

      _setStatus(ConnectionStatus.authenticating);
      socket.emit(ProtocolEvents.authenticate, authPayload);
      final result = await authResult.future.timeout(
        connectTimeout,
        onTimeout: () =>
            throw const ConnectionFailure(ConnectionFailure.timeout),
      );

      if (result['success'] != true) {
        throw ConnectionFailure(
          (result['code'] as String?) ?? ErrorCodes.executionFailed,
          result['message'] as String?,
        );
      }
      _setStatus(ConnectionStatus.ready);
      return result;
    } on ConnectionFailure {
      await _teardown();
      _setStatus(ConnectionStatus.error);
      rethrow;
    }
  }

  void _onCommandResponse(dynamic data) {
    if (_pending.isEmpty) return;
    final map = _asMap(data);
    final payload = map['data'];
    _pending.removeFirst().complete(
      CommandResponse(
        ok: map['ok'] == true,
        code: map['code'] as String?,
        message: (map['message'] ?? map['error']) as String?,
        data: payload is Map ? Map<String, dynamic>.from(payload) : null,
      ),
    );
  }

  void _onKeyboardEvent(dynamic data) {
    final map = _asMap(data);
    final details = _asMap(map['data']);
    _hintController.add(
      KeyboardHint(
        show: map['event'] == 'show',
        window: (details['window'] as String?) ?? '',
      ),
    );
  }

  void _onDisconnected() {
    _failPending();
    if (_closing) return;
    // Unexpected drop: server stopped, device revoked or network lost.
    if (_status == ConnectionStatus.ready ||
        _status == ConnectionStatus.authenticating) {
      _setStatus(ConnectionStatus.error);
      _failureController.add(
        const ConnectionFailure(ConnectionFailure.network),
      );
    }
  }

  void _failPending() {
    while (_pending.isNotEmpty) {
      _pending.removeFirst().complete(CommandResponse.notReady);
    }
  }

  @override
  void fire(Map<String, dynamic> payload) {
    if (!isReady) return;
    // `noack` asks the server not to answer: fired commands never reach the
    // FIFO of pending requests, so responses always match a request().
    _socket?.emit(ProtocolEvents.command, {...payload, 'noack': true});
  }

  @override
  Future<CommandResponse> request(Map<String, dynamic> payload) {
    final socket = _socket;
    if (!isReady || socket == null) {
      return Future.value(CommandResponse.notReady);
    }
    final completer = Completer<CommandResponse>();
    _pending.add(completer);
    socket.emit(ProtocolEvents.command, payload);
    return completer.future.timeout(
      requestTimeout,
      onTimeout: () {
        _pending.remove(completer);
        return const CommandResponse(
          ok: false,
          code: ConnectionFailure.timeout,
          message: 'Timeout',
        );
      },
    );
  }

  @override
  Future<void> disconnect() async {
    _closing = true;
    await _teardown();
    _setStatus(ConnectionStatus.idle);
  }

  Future<void> _teardown() async {
    _failPending();
    final socket = _socket;
    _socket = null;
    if (socket == null) return;
    try {
      socket.clearListeners();
      socket.disconnect();
      socket.dispose();
    } on Object catch (error) {
      debugPrint('Socket teardown failed: $error');
    }
  }

  static Map<String, dynamic> _asMap(dynamic data) {
    if (data is Map) return Map<String, dynamic>.from(data);
    if (data is List && data.isNotEmpty && data.first is Map) {
      return Map<String, dynamic>.from(data.first as Map);
    }
    return <String, dynamic>{};
  }

  Future<void> dispose() async {
    await disconnect();
    await _statusController.close();
    await _hintController.close();
    await _failureController.close();
  }
}
