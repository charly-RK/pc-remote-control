import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/discovery_service.dart';
import 'package:remote_pc/core/network/reconnect_policy.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/storage/server_store.dart';
import 'package:remote_pc/features/connection/domain/qr_payload.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';

import '../helpers/fake_connection.dart';

const _oldEndpoint = ServerEndpoint('192.168.1.5', 5723);
const _newEndpoint = ServerEndpoint('192.168.1.99', 5724);

SavedServer _saved() => const SavedServer(
  serverId: 'srv-1',
  name: 'PC',
  ip: '192.168.1.5',
  port: 5723,
  deviceId: 'dev-1',
  lastSeenIso: '2026-01-01T00:00:00.000',
);

void main() {
  late FakeConnection connection;
  late FakeDiscovery discovery;
  late MemoryStore store;
  late ConnectionController controller;

  setUp(() {
    connection = FakeConnection();
    discovery = FakeDiscovery();
    store = MemoryStore();
    controller = ConnectionController(
      connection: connection,
      discovery: discovery,
      store: store,
      deviceName: 'Test',
      policy: ReconnectPolicy(steps: const [Duration.zero]),
      scanTimeout: Duration.zero,
      wait: (_) async {},
    );
  });

  tearDown(() => controller.dispose());

  test('pairing with QR stores the token and the server', () async {
    final ok = await controller.pairWithQr(
      const QrPayload(
        ip: '192.168.1.5',
        port: 5723,
        code: '123456',
        serverId: 'srv-1',
        name: 'PC',
      ),
    );
    expect(ok, isTrue);
    expect(controller.status, ConnectionStatus.ready);
    expect(controller.inSession, isTrue);
    expect(store.tokens['srv-1'], 'tok-1');
    expect(store.servers['srv-1']!.deviceId, 'dev-1');
    expect(controller.servers.single.name, 'PC');
  });

  test('wrong PIN reports a Spanish error and stores nothing', () async {
    final ok = await controller.pairWithQr(
      const QrPayload(
        ip: '192.168.1.5',
        port: 5723,
        code: '000000',
        serverId: 'srv-1',
      ),
    );
    expect(ok, isFalse);
    expect(controller.status, ConnectionStatus.error);
    expect(controller.errorMessage, 'PIN incorrecto');
    expect(store.tokens, isEmpty);
  });

  test('reconnects with the saved token on the last known address', () async {
    store.servers['srv-1'] = _saved();
    store.tokens['srv-1'] = 'tok-1';
    connection
      ..validToken = 'tok-1'
      ..reachable.add(_oldEndpoint);

    await controller.start();

    expect(controller.status, ConnectionStatus.ready);
    expect(connection.attempts, [_oldEndpoint]);
    expect(discovery.scans, greaterThanOrEqualTo(0));
  });

  test('invalid token is discarded and the user must pair again', () async {
    store.servers['srv-1'] = _saved();
    store.tokens['srv-1'] = 'revoked';
    connection.validToken = 'tok-1';

    await controller.start();

    expect(controller.status, ConnectionStatus.error);
    expect(store.tokens.containsKey('srv-1'), isFalse);
    expect(controller.errorMessage, contains('vincul'));
    expect(controller.inSession, isFalse);
  });

  test(
    'falls back to rediscovery by server id when the address changed',
    () async {
      store.servers['srv-1'] = _saved();
      store.tokens['srv-1'] = 'tok-1';
      connection
        ..validToken = 'tok-1'
        ..reachable.add(_newEndpoint);
      discovery.servers = const [
        DiscoveredServer(
          id: 'srv-1',
          name: 'PC',
          ip: '192.168.1.99',
          port: 5724,
          protocolVersion: 1,
        ),
      ];

      await controller.start();

      expect(controller.status, ConnectionStatus.ready);
      expect(connection.attempts, [_oldEndpoint, _newEndpoint]);
      expect(store.servers['srv-1']!.ip, '192.168.1.99');
      expect(store.servers['srv-1']!.port, 5724);
    },
  );

  test('keeps retrying with backoff while the PC is unreachable', () async {
    store.servers['srv-1'] = _saved();
    store.tokens['srv-1'] = 'tok-1';
    connection.validToken = 'tok-1';
    var waits = 0;
    controller.dispose();
    controller = ConnectionController(
      connection: connection,
      discovery: discovery,
      store: store,
      deviceName: 'Test',
      policy: ReconnectPolicy(steps: const [Duration.zero]),
      scanTimeout: Duration.zero,
      wait: (_) async {
        waits++;
        if (waits == 3) connection.reachable.add(_oldEndpoint);
      },
    );

    await controller.start();

    expect(waits, 3);
    expect(controller.status, ConnectionStatus.ready);
  });

  test(
    'a dropped connection during a session starts the reconnect loop',
    () async {
      store.servers['srv-1'] = _saved();
      store.tokens['srv-1'] = 'tok-1';
      connection
        ..validToken = 'tok-1'
        ..reachable.add(_oldEndpoint);
      await controller.start();
      expect(controller.status, ConnectionStatus.ready);

      connection.drop();
      await Future<void>.delayed(Duration.zero);
      await Future<void>.delayed(Duration.zero);

      expect(controller.inSession, isTrue);
      expect(connection.attempts.length, greaterThanOrEqualTo(2));
      expect(controller.status, ConnectionStatus.ready);
    },
  );

  test('user disconnect stops auto reconnection', () async {
    store.servers['srv-1'] = _saved();
    store.tokens['srv-1'] = 'tok-1';
    connection
      ..validToken = 'tok-1'
      ..reachable.add(_oldEndpoint);
    await controller.start();

    await controller.disconnect();
    controller.onResumed();
    await Future<void>.delayed(Duration.zero);

    expect(controller.status, ConnectionStatus.idle);
    expect(controller.inSession, isFalse);
  });

  test('forget removes the server and its token', () async {
    store.servers['srv-1'] = _saved();
    store.tokens['srv-1'] = 'tok-1';
    await controller.forget('srv-1');
    expect(store.servers, isEmpty);
    expect(store.tokens, isEmpty);
  });
}
