import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/reconnect_policy.dart';
import 'package:remote_pc/core/storage/server_store.dart';
import 'package:remote_pc/features/connection/data/legacy_connection_source.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/fake_connection.dart';

class _FakeLegacy implements LegacyConnectionSource {
  _FakeLegacy(this.value);

  final LegacyConnection? value;

  @override
  Future<LegacyConnection?> take() async => value;
}

ConnectionController _controller(
  FakeConnection connection,
  MemoryStore store,
  LegacyConnectionSource legacy,
) => ConnectionController(
  connection: connection,
  discovery: FakeDiscovery(),
  store: store,
  deviceName: 'Test',
  legacySource: legacy,
  policy: ReconnectPolicy(steps: const [Duration.zero]),
  scanTimeout: Duration.zero,
  wait: (_) async {},
);

void main() {
  group('PrefsLegacyConnectionSource', () {
    test('reads the old keys once and removes them', () async {
      SharedPreferences.setMockInitialValues({
        'last_ip': '192.168.1.7',
        'last_pin': '123456',
        'sensitivity': 2.0,
      });
      final source = PrefsLegacyConnectionSource();

      final first = await source.take();
      expect(first?.ip, '192.168.1.7');
      expect(first?.pin, '123456');

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.containsKey('last_pin'), isFalse);
      expect(prefs.containsKey('last_ip'), isFalse);
      expect(prefs.getDouble('sensitivity'), 2.0);
      expect(await source.take(), isNull);
    });

    test('returns null without legacy data', () async {
      SharedPreferences.setMockInitialValues({});
      expect(await PrefsLegacyConnectionSource().take(), isNull);
    });
  });

  group('legacy import in the controller', () {
    test('pairs with the old PIN and stores a token, not the PIN', () async {
      final connection = FakeConnection();
      final store = MemoryStore();
      final controller = _controller(
        connection,
        store,
        _FakeLegacy(const LegacyConnection(ip: '192.168.1.7', pin: '123456')),
      );

      await controller.start();

      expect(controller.status, ConnectionStatus.ready);
      expect(store.tokens.values, ['tok-1']);
      expect(controller.servers.single.ip, '192.168.1.7');
      expect(controller.servers.single.port, 5723);
    });

    test(
      'a wrong old PIN fails silently and keeps the address prefilled',
      () async {
        final connection = FakeConnection();
        final store = MemoryStore();
        final controller = _controller(
          connection,
          store,
          _FakeLegacy(const LegacyConnection(ip: '192.168.1.7', pin: '000000')),
        );

        await controller.start();

        expect(controller.status, ConnectionStatus.idle);
        expect(controller.errorMessage, isNull);
        expect(controller.prefillHost, '192.168.1.7');
        expect(store.tokens, isEmpty);
      },
    );

    test('is skipped when a server is already saved', () async {
      final connection = FakeConnection();
      final store = MemoryStore();
      store.servers['srv'] = const SavedServer(
        serverId: 'srv',
        name: 'PC',
        ip: '10.0.0.2',
        port: 5723,
        deviceId: 'd',
        lastSeenIso: '2026-01-01T00:00:00.000',
      );
      final controller = _controller(
        connection,
        store,
        _FakeLegacy(const LegacyConnection(ip: '192.168.1.7', pin: '123456')),
      );

      await controller.start();

      expect(connection.attempts.any((e) => e.ip == '192.168.1.7'), isFalse);
    });
  });
}
