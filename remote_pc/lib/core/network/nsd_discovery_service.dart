import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:nsd/nsd.dart' as nsd;
import 'package:remote_pc/core/network/discovery_service.dart';

/// mDNS discovery through the `nsd` plugin. Service type `_pcremote._tcp`,
/// TXT records: id, name, v (see docs/PROTOCOL.md).
class NsdDiscoveryService implements DiscoveryService {
  static const serviceType = '_pcremote._tcp';

  @override
  Future<List<DiscoveredServer>> scan(Duration timeout) async {
    final found = <String, DiscoveredServer>{};
    final subscription = watch().listen((server) => found[server.id] = server);
    await Future<void>.delayed(timeout);
    await subscription.cancel();
    return found.values.toList();
  }

  @override
  Stream<DiscoveredServer> watch() {
    nsd.Discovery? discovery;
    nsd.ServiceListener? listener;
    late final StreamController<DiscoveredServer> controller;

    controller = StreamController<DiscoveredServer>(
      onListen: () async {
        try {
          final started = await nsd.startDiscovery(
            serviceType,
            ipLookupType: nsd.IpLookupType.v4,
          );
          discovery = started;
          void onService(nsd.Service service, nsd.ServiceStatus status) {
            if (status != nsd.ServiceStatus.found) return;
            final server = parseService(service);
            if (server != null && !controller.isClosed) {
              controller.add(server);
            }
          }

          listener = onService;
          started.addServiceListener(onService);
          // Services found before the listener was attached.
          for (final service in started.services) {
            final server = parseService(service);
            if (server != null) controller.add(server);
          }
        } on Object catch (error) {
          debugPrint('Discovery unavailable: $error');
          await controller.close();
        }
      },
      onCancel: () async {
        final current = discovery;
        if (current == null) return;
        if (listener != null) current.removeServiceListener(listener!);
        try {
          await nsd.stopDiscovery(current);
        } on Object catch (error) {
          debugPrint('Stopping discovery failed: $error');
        }
      },
    );
    return controller.stream;
  }

  /// Converts an mDNS service into a [DiscoveredServer]; null if incomplete.
  @visibleForTesting
  static DiscoveredServer? parseService(nsd.Service service) {
    final txt = service.txt ?? const <String, Uint8List?>{};
    final id = _text(txt['id']);
    final port = service.port;
    final addresses = service.addresses ?? const [];
    if (id == null || id.isEmpty || port == null || addresses.isEmpty) {
      return null;
    }
    final ip = addresses
        .firstWhere((a) => a.type.name == 'IPv4', orElse: () => addresses.first)
        .address;
    return DiscoveredServer(
      id: id,
      name: _text(txt['name']) ?? service.name ?? ip,
      ip: ip,
      port: port,
      protocolVersion: int.tryParse(_text(txt['v']) ?? '') ?? 1,
    );
  }

  static String? _text(Uint8List? bytes) {
    if (bytes == null) return null;
    return utf8.decode(bytes, allowMalformed: true);
  }
}
