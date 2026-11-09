import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/reconnect_policy.dart';

void main() {
  test('follows the backoff steps and caps at 30 seconds', () {
    final policy = ReconnectPolicy();
    final delays = List.generate(8, (_) => policy.next().inSeconds);
    expect(delays, [1, 2, 4, 8, 15, 30, 30, 30]);
  });

  test('reset restarts the sequence', () {
    final policy = ReconnectPolicy();
    policy
      ..next()
      ..next();
    expect(policy.attempt, 2);
    policy.reset();
    expect(policy.attempt, 0);
    expect(policy.next(), const Duration(seconds: 1));
  });

  test('accepts custom steps', () {
    final policy = ReconnectPolicy(
      steps: const [Duration(milliseconds: 10), Duration(milliseconds: 20)],
    );
    expect(policy.next(), const Duration(milliseconds: 10));
    expect(policy.next(), const Duration(milliseconds: 20));
    expect(policy.next(), const Duration(milliseconds: 20));
  });
}
