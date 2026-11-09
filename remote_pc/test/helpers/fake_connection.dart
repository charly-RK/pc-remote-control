import 'dart:async';

import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/discovery_service.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/core/storage/server_store.dart';

class FakeConnection implements RemoteConnection {
  /// Endpoints that accept the token. Others fail with [failureFor].
  final Set<ServerEndpoint> reachable = {};
  String? validToken;
  String? failureCode;
  final attempts = <ServerEndpoint>[];
  final _failures = StreamController<ConnectionFailure>.broadcast();
  ConnectionStatus _status = ConnectionStatus.idle;

  @override
  ConnectionStatus get status => _status;
  @override
  Stream<ConnectionStatus> get statusStream => const Stream.empty();
  @override
  Stream<KeyboardHint> get keyboardHints => const Stream.empty();
  @override
  Stream<ConnectionFailure> get failures => _failures.stream;
  @override
  bool get isReady => _status == ConnectionStatus.ready;

  void drop() {
    _status = ConnectionStatus.error;
    _failures.add(const ConnectionFailure(ConnectionFailure.network));
  }

  @override
  Future<PairingOutcome> pair(
    ServerEndpoint endpoint,
    String pin,
    String deviceName,
  ) async {
    attempts.add(endpoint);
    if (pin != '123456') {
      throw const ConnectionFailure(ErrorCodes.invalidPin);
    }
    _status = ConnectionStatus.ready;
    validToken = 'tok-1';
    return const PairingOutcome(token: 'tok-1', deviceId: 'dev-1');
  }

  @override
  Future<void> connectWithToken(ServerEndpoint endpoint, String token) async {
    attempts.add(endpoint);
    if (failureCode != null) throw ConnectionFailure(failureCode!);
    if (token != validToken) {
      throw const ConnectionFailure(ErrorCodes.invalidToken);
    }
    if (!reachable.contains(endpoint)) {
      throw const ConnectionFailure(ConnectionFailure.network);
    }
    _status = ConnectionStatus.ready;
  }

  @override
  Future<void> disconnect() async => _status = ConnectionStatus.idle;

  @override
  void fire(Map<String, dynamic> payload) {}

  @override
  Future<CommandResponse> request(Map<String, dynamic> payload) async =>
      const CommandResponse(ok: true);
}

class FakeDiscovery implements DiscoveryService {
  List<DiscoveredServer> servers = [];
  int scans = 0;

  @override
  Future<List<DiscoveredServer>> scan(Duration timeout) async {
    scans++;
    return servers;
  }

  @override
  Stream<DiscoveredServer> watch() => const Stream.empty();
}

class MemoryStore implements ServerStore {
  final servers = <String, SavedServer>{};
  final tokens = <String, String>{};

  @override
  Future<List<SavedServer>> loadServers() async => servers.values.toList();
  @override
  Future<void> saveServer(SavedServer server) async =>
      servers[server.serverId] = server;
  @override
  Future<void> removeServer(String serverId) async => servers.remove(serverId);
  @override
  Future<String?> readToken(String serverId) async => tokens[serverId];
  @override
  Future<void> saveToken(String serverId, String token) async =>
      tokens[serverId] = token;
  @override
  Future<void> deleteToken(String serverId) async => tokens.remove(serverId);
}
