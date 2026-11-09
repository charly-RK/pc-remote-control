import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/features/media/presentation/controllers/media_controller.dart';

import '../helpers/recording_connection.dart';

void main() {
  late RecordingConnection connection;
  late DateTime now;
  late MediaController media;

  setUp(() {
    connection = RecordingConnection();
    now = DateTime(2026, 1, 1, 12);
    media = MediaController(connection, clock: () => now);
  });

  tearDown(() => media.dispose());

  CommandResponse state({double? volume, bool? muted, bool? playing}) =>
      CommandResponse(
        ok: true,
        data: {'volume': volume, 'muted': muted, 'playing': playing},
      );

  test('refresh applies volume, muted and playing from the PC', () async {
    connection.onRequest = (_) =>
        state(volume: 0.3, muted: true, playing: true);
    await media.refresh();
    expect(connection.requested.single, {
      'action': 'media_control',
      'command': 'get_state',
    });
    expect(media.volume, 0.3);
    expect(media.muted, isTrue);
    expect(media.playing, isTrue);
  });

  test('null fields keep the last known value', () async {
    connection.onRequest = (_) => state(volume: 0.7);
    await media.refresh();
    connection.onRequest = (_) => state();
    await media.refresh();
    expect(media.volume, 0.7);
    expect(media.playing, isFalse);
  });

  test('volume buttons apply the fresh volume from the response', () async {
    connection.onRequest = (_) => state(volume: 0.52);
    await media.send(MediaCommand.volumeUp);
    expect(connection.requested.single['command'], 'volume_up');
    expect(media.volume, 0.52);
  });

  test(
    'play/pause is optimistic and polled playing is ignored for 2.5 s',
    () async {
      connection.onRequest = (_) => state(playing: false);
      final pending = media.send(MediaCommand.playPause);
      expect(media.playing, isTrue, reason: 'toggled before the response');
      await pending;
      expect(
        media.playing,
        isTrue,
        reason: 'the lagging PC state must not flip it back',
      );

      now = now.add(const Duration(milliseconds: 1000));
      await media.refresh();
      expect(media.playing, isTrue);

      now = now.add(const Duration(milliseconds: 2000));
      await media.refresh();
      expect(
        media.playing,
        isFalse,
        reason: 'after the hold the PC state wins',
      );
    },
  );

  test('extra controls are fire and forget', () async {
    await media.send(MediaCommand.gameBar);
    expect(connection.requested, isEmpty);
    expect(connection.fired.single['command'], 'game_bar');
  });

  testWidgets(
    'slider drag updates locally, coalesces sends and sends the final value',
    (tester) async {
      media.volumeChanged(0.1); // sent at once
      media.volumeChanged(0.2); // within 60 ms: coalesced
      media.volumeChanged(0.3);
      expect(media.volume, 0.3);
      expect(connection.fired.length, 1);

      now = now.add(const Duration(milliseconds: 70));
      await tester.pump(const Duration(milliseconds: 70));
      expect(connection.fired.length, 2);
      expect(connection.fired.last['level'], 0.3);

      media.volumeChangeEnd(0.4);
      expect(connection.fired.last['level'], 0.4);
    },
  );

  test('server data does not overwrite the slider while dragging', () async {
    media.volumeChanged(0.9);
    connection.onRequest = (_) => state(volume: 0.2);
    await media.refresh();
    expect(media.volume, 0.9);
    media.volumeChangeEnd(0.9);
    await media.refresh();
    expect(media.volume, 0.2);
  });
}
