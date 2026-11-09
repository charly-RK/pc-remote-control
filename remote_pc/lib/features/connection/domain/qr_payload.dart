import 'dart:convert';

import 'package:remote_pc/core/protocol/protocol.dart';

/// Content of the QR shown by the server: {ip, port, code, id, name, v}.
/// `id` and `name` are optional for older servers.
class QrPayload {
  const QrPayload({
    required this.ip,
    required this.port,
    required this.code,
    this.serverId,
    this.name,
    this.version = protocolVersion,
  });

  final String ip;
  final int port;
  final String code;
  final String? serverId;
  final String? name;
  final int version;

  /// Returns null when [raw] is not a valid PC Remote QR.
  static QrPayload? tryParse(String? raw) {
    if (raw == null || raw.isEmpty) return null;
    final Object? decoded;
    try {
      decoded = jsonDecode(raw);
    } on FormatException {
      return null;
    }
    if (decoded is! Map) return null;
    final ip = decoded['ip'];
    final port = decoded['port'];
    final code = decoded['code'];
    if (ip is! String || ip.trim().isEmpty) return null;
    if (port is! int || port < 1 || port > 65535) return null;
    if (code is! String || code.isEmpty) return null;
    final id = decoded['id'];
    final name = decoded['name'];
    final version = decoded['v'];
    return QrPayload(
      ip: ip.trim(),
      port: port,
      code: code,
      serverId: id is String && id.isNotEmpty ? id : null,
      name: name is String && name.isNotEmpty ? name : null,
      version: version is int ? version : protocolVersion,
    );
  }

  /// Tolerant parser kept from the original app: accepts malformed JSON that
  /// still contains `"ip"` and `"code"` (the port then defaults).
  static QrPayload? tryParseLenient(String? raw) {
    final strict = tryParse(raw);
    if (strict != null) return strict;
    if (raw == null || !raw.trim().startsWith('{')) return null;
    final ip = RegExp(r'"ip":\s*"([^"]+)"').firstMatch(raw)?.group(1);
    final code = RegExp(r'"code":\s*"([^"]+)"').firstMatch(raw)?.group(1);
    if (ip == null || code == null) return null;
    final port = int.tryParse(
      RegExp(r'"port":\s*(\d+)').firstMatch(raw)?.group(1) ?? '',
    );
    return QrPayload(
      ip: ip.trim(),
      port: port ?? defaultServerPort,
      code: code,
    );
  }
}
