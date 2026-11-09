import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/features/connection/domain/manual_input.dart';
import 'package:remote_pc/features/connection/domain/qr_payload.dart';

void main() {
  group('QrPayload', () {
    test('parses a complete payload', () {
      final payload = QrPayload.tryParse(
        jsonEncode({
          'ip': '192.168.1.5',
          'port': 5723,
          'code': '123456',
          'id': 'abc123',
          'name': 'PC',
          'v': 1,
        }),
      );
      expect(payload, isNotNull);
      expect(payload!.ip, '192.168.1.5');
      expect(payload.port, 5723);
      expect(payload.code, '123456');
      expect(payload.serverId, 'abc123');
      expect(payload.name, 'PC');
    });

    test('id and name are optional (older servers)', () {
      final payload = QrPayload.tryParse(
        jsonEncode({'ip': '10.0.0.2', 'port': 5000, 'code': '111111'}),
      );
      expect(payload, isNotNull);
      expect(payload!.serverId, isNull);
      expect(payload.name, isNull);
    });

    test('rejects invalid content', () {
      expect(QrPayload.tryParse(null), isNull);
      expect(QrPayload.tryParse(''), isNull);
      expect(QrPayload.tryParse('not json'), isNull);
      expect(QrPayload.tryParse('[1,2]'), isNull);
      expect(
        QrPayload.tryParse(jsonEncode({'ip': '', 'port': 1, 'code': '1'})),
        isNull,
      );
      expect(
        QrPayload.tryParse(jsonEncode({'ip': 'a', 'port': 0, 'code': '1'})),
        isNull,
      );
      expect(
        QrPayload.tryParse(jsonEncode({'ip': 'a', 'port': 70000, 'code': '1'})),
        isNull,
      );
      expect(QrPayload.tryParse(jsonEncode({'ip': 'a', 'port': 1})), isNull);
    });
  });

  group('ManualInput', () {
    test('validates host, port and pin', () {
      expect(ManualInput.validate('', '5723', '123456'), InputProblem.host);
      expect(ManualInput.validate('a b', '5723', '123456'), InputProblem.host);
      expect(
        ManualInput.validate('192.168.1.5', 'abc', '123456'),
        InputProblem.port,
      );
      expect(
        ManualInput.validate('192.168.1.5', '70000', '123456'),
        InputProblem.port,
      );
      expect(
        ManualInput.validate('192.168.1.5', '5723', '12'),
        InputProblem.pin,
      );
      expect(ManualInput.validate('192.168.1.5', '5723', '123456'), isNull);
    });

    test('tryCreate trims values', () {
      final input = ManualInput.tryCreate(' 10.0.0.1 ', ' 5723 ', ' 123456 ');
      expect(input!.host, '10.0.0.1');
      expect(input.port, 5723);
      expect(input.pin, '123456');
    });
  });
}
