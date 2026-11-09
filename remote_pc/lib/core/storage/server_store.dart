import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SavedServer {
  const SavedServer({
    required this.serverId,
    required this.name,
    required this.ip,
    required this.port,
    required this.deviceId,
    required this.lastSeenIso,
  });

  final String serverId;
  final String name;
  final String ip;
  final int port;
  final String deviceId;
  final String lastSeenIso;

  SavedServer copyWith({
    String? name,
    String? ip,
    int? port,
    String? lastSeenIso,
  }) => SavedServer(
    serverId: serverId,
    name: name ?? this.name,
    ip: ip ?? this.ip,
    port: port ?? this.port,
    deviceId: deviceId,
    lastSeenIso: lastSeenIso ?? this.lastSeenIso,
  );

  Map<String, dynamic> toJson() => {
    'serverId': serverId,
    'name': name,
    'ip': ip,
    'port': port,
    'deviceId': deviceId,
    'lastSeenIso': lastSeenIso,
  };

  static SavedServer? tryFromJson(Object? raw) {
    if (raw is! Map) return null;
    final serverId = raw['serverId'];
    final name = raw['name'];
    final ip = raw['ip'];
    final port = raw['port'];
    final deviceId = raw['deviceId'];
    if (serverId is! String ||
        name is! String ||
        ip is! String ||
        port is! int ||
        deviceId is! String) {
      return null;
    }
    return SavedServer(
      serverId: serverId,
      name: name,
      ip: ip,
      port: port,
      deviceId: deviceId,
      lastSeenIso: (raw['lastSeenIso'] as String?) ?? '',
    );
  }
}

/// Persistence for paired servers. Tokens are credentials and live apart from
/// the server list.
abstract class ServerStore {
  Future<List<SavedServer>> loadServers();
  Future<void> saveServer(SavedServer server);
  Future<void> removeServer(String serverId);
  Future<String?> readToken(String serverId);
  Future<void> saveToken(String serverId, String token);
  Future<void> deleteToken(String serverId);
}

/// shared_preferences for the list, flutter_secure_storage for tokens.
/// If storage fails the app keeps working for the current session using
/// in-memory copies.
class PersistentServerStore implements ServerStore {
  PersistentServerStore({FlutterSecureStorage? secureStorage})
    : _secure = secureStorage ?? const FlutterSecureStorage();

  static const _serversKey = 'saved_servers';
  static const _tokenPrefix = 'token_';

  final FlutterSecureStorage _secure;
  final Map<String, String> _memoryTokens = {};
  List<SavedServer>? _memoryServers;

  @override
  Future<List<SavedServer>> loadServers() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_serversKey);
      if (raw == null) return _memoryServers ?? [];
      final decoded = jsonDecode(raw);
      if (decoded is! List) return [];
      final servers = decoded
          .map(SavedServer.tryFromJson)
          .whereType<SavedServer>()
          .toList();
      _memoryServers = servers;
      return servers;
    } on Object catch (error) {
      debugPrint('Loading saved servers failed: $error');
      return _memoryServers ?? [];
    }
  }

  Future<void> _persist(List<SavedServer> servers) async {
    _memoryServers = servers;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
        _serversKey,
        jsonEncode(servers.map((s) => s.toJson()).toList()),
      );
    } on Object catch (error) {
      debugPrint('Saving servers failed: $error');
    }
  }

  @override
  Future<void> saveServer(SavedServer server) async {
    final servers = await loadServers();
    final index = servers.indexWhere((s) => s.serverId == server.serverId);
    if (index >= 0) {
      servers[index] = server;
    } else {
      servers.add(server);
    }
    await _persist(servers);
  }

  @override
  Future<void> removeServer(String serverId) async {
    final servers = await loadServers();
    servers.removeWhere((s) => s.serverId == serverId);
    await _persist(servers);
  }

  @override
  Future<String?> readToken(String serverId) async {
    try {
      final value = await _secure.read(key: '$_tokenPrefix$serverId');
      if (value != null) return value;
    } on Object catch (error) {
      debugPrint('Reading token failed: $error');
    }
    return _memoryTokens[serverId];
  }

  @override
  Future<void> saveToken(String serverId, String token) async {
    _memoryTokens[serverId] = token;
    try {
      await _secure.write(key: '$_tokenPrefix$serverId', value: token);
    } on Object catch (error) {
      debugPrint('Saving token failed: $error');
    }
  }

  @override
  Future<void> deleteToken(String serverId) async {
    _memoryTokens.remove(serverId);
    try {
      await _secure.delete(key: '$_tokenPrefix$serverId');
    } on Object catch (error) {
      debugPrint('Deleting token failed: $error');
    }
  }
}
