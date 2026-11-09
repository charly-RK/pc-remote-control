import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/features/connection/domain/qr_payload.dart';

void main() {
  test('lenient parsing reads a strict payload', () {
    final qr = QrPayload.tryParseLenient(
      '{"ip":"10.0.0.5","port":5723,"code":"123456","id":"abc","v":1}',
    );
    expect(qr?.ip, '10.0.0.5');
    expect(qr?.serverId, 'abc');
  });

  test('lenient parsing recovers ip and code from malformed JSON', () {
    final qr = QrPayload.tryParseLenient('{"ip": "10.0.0.5", "code": "123456"');
    expect(qr?.ip, '10.0.0.5');
    expect(qr?.code, '123456');
    expect(qr?.port, defaultServerPort);
  });

  test('lenient parsing rejects other content', () {
    expect(QrPayload.tryParseLenient('http://10.0.0.5:5723'), isNull);
    expect(QrPayload.tryParseLenient('{"foo": 1}'), isNull);
    expect(QrPayload.tryParseLenient(null), isNull);
  });
}
