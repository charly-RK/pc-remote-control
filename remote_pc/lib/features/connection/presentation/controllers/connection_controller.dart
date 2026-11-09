import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:remote_pc/core/background/background_keep_alive.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/discovery_service.dart';
import 'package:remote_pc/core/network/reconnect_policy.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/core/storage/server_store.dart';
import 'package:remote_pc/features/connection/data/legacy_connection_source.dart';
import 'package:remote_pc/features/connection/domain/manual_input.dart';
import 'package:remote_pc/features/connection/domain/qr_payload.dart';
import 'package:remote_pc/features/connection/presentation/connection_strings.dart';

enum _Outcome { connected, retry, fatal }

/// Orchestrates pairing, token reconnection, rediscovery and the auto
/// reconnect loop. Widgets only read its state and call its methods.
class ConnectionController extends ChangeNotifier {
  ConnectionController({
    required this.connection,
    required this.discovery,
    required this.store,
    required this.deviceName,
    this.keepAlive = const NoopBackgroundKeepAlive(),
    this.legacySource,
    ReconnectPolicy? policy,
    this.scanTimeout = const Duration(seconds: 3),
    Future<void> Function(Duration)? wait,
    DateTime Function()? clock,
  }) : _policy = policy ?? ReconnectPolicy(),
       _wait = wait ?? ((d) => Future<void>.delayed(d)),
       _clock = clock ?? DateTime.now {
    _failureSub = connection.failures.listen(_onConnectionDropped);
  }

  final RemoteConnection connection;
  final DiscoveryService discovery;
  final ServerStore store;
  final String deviceName;
  final BackgroundKeepAlive keepAlive;
  final LegacyConnectionSource? legacySource;
  final Duration scanTimeout;

  final ReconnectPolicy _policy;
  final Future<void> Function(Duration) _wait;
  final DateTime Function() _clock;

  StreamSubscription<ConnectionFailure>? _failureSub;
  Future<List<DiscoveredServer>>? _scanFuture;

  ConnectionStatus _status = ConnectionStatus.idle;
  List<SavedServer> _servers = const [];
  List<DiscoveredServer> _discovered = const [];
  SavedServer? _current;
  String? _error;
  bool _scanning = false;
  bool _inSession = false;
  bool _userDisconnected = false;
  bool _loopRunning = false;
  bool _disposed = false;
  bool _keepAliveOn = false;
  String? _legacyHost;
  int _generation = 0;

  ConnectionStatus get status => _status;
  List<SavedServer> get servers => _servers;

  /// Discovered servers that are not already saved.
  List<DiscoveredServer> get nearby => _discovered
      .where((d) => !_servers.any((s) => s.serverId == d.id))
      .toList();

  SavedServer? get current => _current;
  String? get errorMessage => _error;
  bool get scanning => _scanning;

  /// True when the session is fully authenticated.
  bool get isAuthenticated => _status == ConnectionStatus.ready;

  /// Every server seen on the network in the last scan.
  List<DiscoveredServer> get discovered => _discovered;

  /// Address to prefill in the connection form: the last server used or the
  /// IP imported from the first version of the app.
  String? get prefillHost => _servers.firstOrNull?.ip ?? _legacyHost;

  /// Port to use for [host]: the discovered one when the host was found by
  /// discovery, otherwise the default.
  int portFor(String host) =>
      _discovered.where((d) => d.ip == host).firstOrNull?.port ??
      _servers.where((s) => s.ip == host).firstOrNull?.port ??
      defaultServerPort;

  /// True once a connection was established and the user has not left it.
  /// While true the control screens stay visible during reconnection.
  bool get inSession => _inSession;

  bool get isBusy =>
      _status == ConnectionStatus.connecting ||
      _status == ConnectionStatus.authenticating ||
      _status == ConnectionStatus.searching ||
      _status == ConnectionStatus.reconnecting;

  // ---------------------------------------------------------------- start

  /// Loads saved servers and connects to the most recently used one.
  Future<void> start() async {
    await _reloadServers();
    unawaited(scanLan());
    final last = _servers.firstOrNull;
    if (last != null && !_userDisconnected) {
      await _startLoop(last);
    } else if (last == null) {
      await _importLegacy();
    }
  }

  /// One-time import of the connection saved by the first version of the
  /// app: pairs again with the old PIN and stores the token.
  Future<void> _importLegacy() async {
    final legacy = await legacySource?.take();
    if (legacy == null || _disposed) return;
    _legacyHost = legacy.ip;
    for (final port in const [defaultServerPort, 5000]) {
      final paired = await _pair(ServerEndpoint(legacy.ip, port), legacy.pin);
      if (paired) return;
    }
    // A silent failure: the user simply sees the prefilled address.
    _error = null;
    _setStatus(ConnectionStatus.idle);
  }

  Future<void> scanLan() async {
    _scanning = true;
    _notify();
    _discovered = await _runScan();
    _scanning = false;
    _notify();
  }

  Future<List<DiscoveredServer>> _runScan() {
    // One scan at a time: the discovery plugin does not allow parallel ones.
    return _scanFuture ??= _scan().whenComplete(() => _scanFuture = null);
  }

  Future<List<DiscoveredServer>> _scan() async {
    try {
      return await discovery.scan(scanTimeout);
    } on Object catch (error) {
      debugPrint('Discovery scan failed: $error');
      return const [];
    }
  }

  // -------------------------------------------------------------- actions

  Future<void> connectSaved(SavedServer server) {
    _userDisconnected = false;
    return _startLoop(server);
  }

  Future<bool> pairWithQr(QrPayload qr) => _pair(
    ServerEndpoint(qr.ip, qr.port),
    qr.code,
    serverId: qr.serverId,
    name: qr.name,
  );

  Future<bool> pairManual(ManualInput input) =>
      _pair(ServerEndpoint(input.host, input.port), input.pin);

  Future<bool> pairDiscovered(DiscoveredServer server, String pin) => _pair(
    ServerEndpoint(server.ip, server.port),
    pin,
    serverId: server.id,
    name: server.name,
  );

  /// User initiated: stops any reconnect loop and closes the connection.
  Future<void> disconnect() async {
    _generation++;
    _loopRunning = false;
    _userDisconnected = true;
    _inSession = false;
    _current = null;
    _error = null;
    await connection.disconnect();
    _setStatus(ConnectionStatus.idle);
  }

  Future<void> forget(String serverId) async {
    if (_current?.serverId == serverId) await disconnect();
    await store.deleteToken(serverId);
    await store.removeServer(serverId);
    await _reloadServers();
  }

  /// Call when the app returns to the foreground.
  void onResumed() {
    if (_disposed || _loopRunning || _userDisconnected) return;
    if (_status == ConnectionStatus.ready &&
        connection.status == ConnectionStatus.ready) {
      return;
    }
    final target = _current ?? _servers.firstOrNull;
    if (target != null) unawaited(_startLoop(target));
  }

  // ----------------------------------------------------------- internals

  Future<bool> _pair(
    ServerEndpoint endpoint,
    String pin, {
    String? serverId,
    String? name,
  }) async {
    final generation = ++_generation;
    _loopRunning = false;
    _userDisconnected = false;
    _error = null;
    _setStatus(ConnectionStatus.connecting);
    try {
      final outcome = await connection.pair(endpoint, pin, deviceName);
      if (generation != _generation) {
        await connection.disconnect();
        return false;
      }
      final id =
          serverId ??
          _knownIdFor(endpoint) ??
          'manual:${endpoint.ip}:${endpoint.port}';
      final server = SavedServer(
        serverId: id,
        name: name ?? _knownNameFor(endpoint) ?? endpoint.ip,
        ip: endpoint.ip,
        port: endpoint.port,
        deviceId: outcome.deviceId,
        lastSeenIso: _clock().toIso8601String(),
      );
      await store.saveToken(id, outcome.token);
      await store.saveServer(server);
      await _reloadServers();
      _current = server;
      _inSession = true;
      _policy.reset();
      _setStatus(ConnectionStatus.ready);
      return true;
    } on ConnectionFailure catch (failure) {
      if (generation == _generation) {
        _error = ConnectionStrings.forFailure(failure);
        _setStatus(ConnectionStatus.error);
      }
      return false;
    }
  }

  String? _knownIdFor(ServerEndpoint endpoint) => _discovered
      .where((d) => d.ip == endpoint.ip && d.port == endpoint.port)
      .firstOrNull
      ?.id;

  String? _knownNameFor(ServerEndpoint endpoint) => _discovered
      .where((d) => d.ip == endpoint.ip && d.port == endpoint.port)
      .firstOrNull
      ?.name;

  void _onConnectionDropped(ConnectionFailure failure) {
    if (_disposed || !_inSession || _loopRunning || _userDisconnected) return;
    final target = _current;
    if (target != null) unawaited(_startLoop(target));
  }

  Future<void> _startLoop(SavedServer server) async {
    final generation = ++_generation;
    _current = server;
    _policy.reset();
    _error = null;
    await _runLoop(server, generation);
  }

  bool _isActive(int generation) => !_disposed && generation == _generation;

  Future<void> _runLoop(SavedServer server, int generation) async {
    _loopRunning = true;
    try {
      var first = true;
      while (_isActive(generation)) {
        _setStatus(
          first && !_inSession
              ? ConnectionStatus.connecting
              : ConnectionStatus.reconnecting,
        );
        final outcome = await _attempt(server, generation);
        if (!_isActive(generation)) return;
        switch (outcome) {
          case _Outcome.connected:
            _policy.reset();
            _inSession = true;
            _error = null;
            _setStatus(ConnectionStatus.ready);
            return;
          case _Outcome.fatal:
            _inSession = false;
            _setStatus(ConnectionStatus.error);
            return;
          case _Outcome.retry:
            first = false;
            _setStatus(ConnectionStatus.reconnecting);
            await _wait(_policy.next());
        }
      }
    } finally {
      if (generation == _generation) _loopRunning = false;
    }
  }

  /// One full attempt: saved token on the last known address, then
  /// rediscovery by server id.
  Future<_Outcome> _attempt(SavedServer server, int generation) async {
    final token = await store.readToken(server.serverId);
    if (token == null) {
      _error = ConnectionStrings.forFailure(
        const ConnectionFailure(ErrorCodes.invalidToken),
      );
      return _Outcome.fatal;
    }

    var failure = await _tryToken(server.ip, server.port, token);
    if (failure == null) {
      await _markSeen(server, server.ip, server.port);
      return _Outcome.connected;
    }
    if (!_isActive(generation)) return _Outcome.retry;
    final fatal = await _handleFatal(server, failure);
    if (fatal) return _Outcome.fatal;

    _setStatus(ConnectionStatus.searching);
    final found = (await _runScan())
        .where((d) => d.id == server.serverId)
        .firstOrNull;
    if (!_isActive(generation)) return _Outcome.retry;
    if (found != null && (found.ip != server.ip || found.port != server.port)) {
      failure = await _tryToken(found.ip, found.port, token);
      if (failure == null) {
        await _markSeen(server, found.ip, found.port);
        return _Outcome.connected;
      }
      if (await _handleFatal(server, failure)) return _Outcome.fatal;
    }
    _error = ConnectionStrings.forFailure(failure);
    return _Outcome.retry;
  }

  Future<ConnectionFailure?> _tryToken(
    String ip,
    int port,
    String token,
  ) async {
    try {
      await connection.connectWithToken(ServerEndpoint(ip, port), token);
      return null;
    } on ConnectionFailure catch (failure) {
      return failure;
    }
  }

  /// Failures that retrying cannot fix. Returns true when the loop must stop.
  Future<bool> _handleFatal(
    SavedServer server,
    ConnectionFailure failure,
  ) async {
    if (failure.code == ErrorCodes.invalidToken) {
      await store.deleteToken(server.serverId);
      _error = ConnectionStrings.forFailure(failure);
      return true;
    }
    if (failure.code == ErrorCodes.rateLimited) {
      _error = ConnectionStrings.forFailure(failure);
      return true;
    }
    return false;
  }

  Future<void> _markSeen(SavedServer server, String ip, int port) async {
    final updated = server.copyWith(
      ip: ip,
      port: port,
      lastSeenIso: _clock().toIso8601String(),
    );
    _current = updated;
    await store.saveServer(updated);
    await _reloadServers();
  }

  Future<void> _reloadServers() async {
    final loaded = await store.loadServers();
    loaded.sort((a, b) => b.lastSeenIso.compareTo(a.lastSeenIso));
    _servers = loaded;
    _notify();
  }

  void _setStatus(ConnectionStatus value) {
    _status = value;
    _syncKeepAlive();
    _notify();
  }

  /// The foreground service runs from the first ready state until the user
  /// leaves the session (it survives short automatic reconnections).
  void _syncKeepAlive() {
    if (_status == ConnectionStatus.ready && _current != null) {
      _keepAliveOn = true;
      final target = _current!;
      unawaited(
        keepAlive.start(
          ConnectionStrings.connectedTo(
            target.name.isNotEmpty ? target.name : target.ip,
          ),
        ),
      );
    } else if (_keepAliveOn && !_inSession) {
      _keepAliveOn = false;
      unawaited(keepAlive.stop());
    }
  }

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _generation++;
    _failureSub?.cancel();
    super.dispose();
  }
}
