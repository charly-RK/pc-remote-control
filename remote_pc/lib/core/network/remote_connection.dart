import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/connection_status.dart';

class ServerEndpoint {
  const ServerEndpoint(this.ip, this.port);

  final String ip;
  final int port;

  String get url => 'http://$ip:$port';

  @override
  bool operator ==(Object other) =>
      other is ServerEndpoint && other.ip == ip && other.port == port;

  @override
  int get hashCode => Object.hash(ip, port);

  @override
  String toString() => '$ip:$port';
}

class PairingOutcome {
  const PairingOutcome({required this.token, required this.deviceId});

  final String token;
  final String deviceId;
}

class KeyboardHint {
  const KeyboardHint({required this.show, required this.window});

  final bool show;
  final String window;
}

/// Why a connection or authentication attempt failed. [code] is one of
/// the protocol error codes or a local code (`NETWORK`, `TIMEOUT`).
class ConnectionFailure implements Exception {
  const ConnectionFailure(this.code, [this.message]);

  static const network = 'NETWORK';
  static const timeout = 'TIMEOUT';

  final String code;
  final String? message;

  @override
  String toString() => 'ConnectionFailure($code, $message)';
}

abstract class RemoteConnection implements CommandSender {
  ConnectionStatus get status;
  Stream<ConnectionStatus> get statusStream;
  Stream<KeyboardHint> get keyboardHints;

  /// Failures that happen after a connection was established (for example the
  /// server revoked this device and dropped the socket).
  Stream<ConnectionFailure> get failures;

  /// First connection: authenticates with the PIN and returns the token.
  /// Throws [ConnectionFailure].
  Future<PairingOutcome> pair(
    ServerEndpoint endpoint,
    String pin,
    String deviceName,
  );

  /// Reconnection with a previously issued token. Throws [ConnectionFailure].
  Future<void> connectWithToken(ServerEndpoint endpoint, String token);

  Future<void> disconnect();
}
