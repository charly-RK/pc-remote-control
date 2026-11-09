import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/hidden_text_bridge.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';

import '../helpers/recording_connection.dart';

void main() {
  late RecordingConnection connection;
  late KeyboardOverlayController overlay;

  setUp(() {
    connection = RecordingConnection();
    overlay = KeyboardOverlayController(
      connection: connection,
      deleteDelay: const Duration(milliseconds: 10),
    );
  });

  tearDown(() async {
    overlay.dispose();
    await connection.close();
  });

  test('a show hint tracks the window but never opens the keyboard', () async {
    connection.emitHint(const KeyboardHint(show: true, window: 'Notepad'));
    await Future<void>.delayed(Duration.zero);
    expect(overlay.currentWindow, 'Notepad');
    expect(overlay.showNativeKeyboard, isFalse);

    connection.emitHint(const KeyboardHint(show: false, window: 'Notepad'));
    await Future<void>.delayed(Duration.zero);
    expect(overlay.currentWindow, isNull);
  });

  test('toggle, show and hide change the visibility', () {
    overlay.toggle();
    expect(overlay.showNativeKeyboard, isTrue);
    overlay.hide();
    expect(overlay.showNativeKeyboard, isFalse);
    overlay.show();
    expect(overlay.showNativeKeyboard, isTrue);
  });

  test(
    'losing the connection hides the keyboard and marks it not ready',
    () async {
      overlay.show();
      expect(overlay.isReady, isTrue);
      connection.emitStatus(ConnectionStatus.reconnecting);
      await Future<void>.delayed(Duration.zero);
      expect(overlay.isReady, isFalse);
      expect(overlay.showNativeKeyboard, isFalse);
    },
  );

  test('the floating button position is stored and notifies', () {
    var notifications = 0;
    overlay.addListener(() => notifications++);
    overlay.keyboardButtonPosition = const Offset(30, 40);
    expect(overlay.keyboardButtonPosition, const Offset(30, 40));
    expect(notifications, 1);
  });

  test('deleteText sends Ctrl+A and then Backspace', () async {
    overlay.deleteText();
    expect(connection.fired, [
      {'action': 'key_press', 'key': 'a', 'ctrl': true},
    ]);
    await Future<void>.delayed(const Duration(milliseconds: 40));
    expect(connection.fired.last, {'action': 'key_press', 'key': 'backspace'});
    expect(connection.fired.length, 2);
  });

  testWidgets(
    'hidden text bridge types new characters and restores the buffer',
    (tester) async {
      final bridge = HiddenTextBridge(connection);
      addTearDown(bridge.dispose);

      bridge.controller.text = '${HiddenTextBridge.buffer}hi';
      await tester.pump();
      expect(connection.fired, [
        {'action': 'text_input', 'text': 'hi'},
      ]);
      expect(bridge.controller.text, HiddenTextBridge.buffer);
    },
  );

  testWidgets('hidden text bridge turns deletions into backspaces', (
    tester,
  ) async {
    final bridge = HiddenTextBridge(connection);
    addTearDown(bridge.dispose);

    bridge.controller.text = '\u200b\u200b';
    await tester.pump();
    expect(connection.fired, [
      {'action': 'key_press', 'key': 'backspace'},
    ]);
    expect(bridge.controller.text, HiddenTextBridge.buffer);
  });

  testWidgets('hidden text bridge submit sends Enter', (tester) async {
    final bridge = HiddenTextBridge(connection);
    addTearDown(bridge.dispose);
    bridge.submit();
    expect(connection.fired, [
      {'action': 'key_press', 'key': 'enter'},
    ]);
  });
}
