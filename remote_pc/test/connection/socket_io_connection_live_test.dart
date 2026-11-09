// Live test against a running PC Remote server. Skipped unless the
// environment variables PCREMOTE_HOST, PCREMOTE_PORT and PCREMOTE_PIN are set.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/network/socket_io_connection.dart';
import 'package:remote_pc/core/protocol/protocol.dart';

void main() {
  final host = Platform.environment['PCREMOTE_HOST'];
  final port = int.tryParse(Platform.environment['PCREMOTE_PORT'] ?? '');
  final pin = Platform.environment['PCREMOTE_PIN'];
  final enabled = host != null && port != null && pin != null;

  test(
    'pairs, reconnects with the token and sends a harmless command',
    () async {
      final endpoint = ServerEndpoint(host!, port!);
      final connection = SocketIoConnection();

      // Wrong PIN is rejected with a code.
      await expectLater(
        connection.pair(endpoint, '000000', 'live-test'),
        throwsA(
          isA<ConnectionFailure>().having(
            (f) => f.code,
            'code',
            ErrorCodes.invalidPin,
          ),
        ),
      );

      final outcome = await connection.pair(endpoint, pin!, 'live-test');
      expect(outcome.token, isNotEmpty);
      expect(outcome.deviceId, isNotEmpty);
      expect(connection.status, ConnectionStatus.ready);

      final response = await connection.request(Commands.mouseMove(0, 0));
      expect(response.ok, isTrue);

      final bad = await connection.request({
        'action': 'media_control',
        'command': 'alt+f4',
      });
      expect(bad.ok, isFalse);
      expect(bad.code, ErrorCodes.invalidPayload);

      await connection.disconnect();
      expect(connection.status, ConnectionStatus.idle);

      await connection.connectWithToken(endpoint, outcome.token);
      expect(connection.status, ConnectionStatus.ready);
      await connection.disconnect();

      await expectLater(
        connection.connectWithToken(endpoint, 'not-a-token'),
        throwsA(
          isA<ConnectionFailure>().having(
            (f) => f.code,
            'code',
            ErrorCodes.invalidToken,
          ),
        ),
      );
      await connection.dispose();
    },
    skip: enabled ? false : 'Set PCREMOTE_HOST, PCREMOTE_PORT, PCREMOTE_PIN',
  );
}
