class DiscoveredServer {
  const DiscoveredServer({
    required this.id,
    required this.name,
    required this.ip,
    required this.port,
    required this.protocolVersion,
  });

  final String id;
  final String name;
  final String ip;
  final int port;
  final int protocolVersion;
}

/// Finds PC Remote servers on the local network (mDNS).
abstract class DiscoveryService {
  /// One-shot scan that completes after [timeout].
  Future<List<DiscoveredServer>> scan(Duration timeout);

  /// Continuous discovery; emits each server as it appears.
  Stream<DiscoveredServer> watch();
}
