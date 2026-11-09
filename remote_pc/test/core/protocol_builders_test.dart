import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/protocol/protocol.dart';

void main() {
  group('Commands', () {
    test('mouse commands', () {
      expect(Commands.mouseMove(3, -4), {
        'action': 'mouse_move',
        'x': 3,
        'y': -4,
      });
      expect(Commands.mouseClick(MouseButton.right, ClickType.double), {
        'action': 'mouse_click',
        'button': 'right',
        'type': 'double',
      });
      expect(Commands.mouseScroll(dy: 5), {
        'action': 'mouse_scroll',
        'dx': 0,
        'dy': 5,
      });
    });

    test(
      'plain key press uses key_press, held keys use the state as action',
      () {
        expect(Commands.key('a'), {'action': 'key_press', 'key': 'a'});
        expect(Commands.key('a', state: KeyState.down), {
          'action': 'down',
          'key': 'a',
        });
      },
    );

    test('hotkey includes only the active modifiers', () {
      expect(Commands.key('c', ctrl: true, shift: true), {
        'action': 'key_press',
        'key': 'c',
        'ctrl': true,
        'shift': true,
      });
    });

    test('text input', () {
      expect(Commands.text('hola'), {'action': 'text_input', 'text': 'hola'});
    });

    test('media sends level only for set_volume', () {
      expect(Commands.media(MediaCommand.mute), {
        'action': 'media_control',
        'command': 'mute',
      });
      expect(Commands.media(MediaCommand.setVolume, level: 0.4), {
        'action': 'media_control',
        'command': 'set_volume',
        'level': 0.4,
      });
      expect(
        Commands.media(MediaCommand.mute, level: 0.4).containsKey('level'),
        isFalse,
      );
    });

    test('system commands and destructive flag', () {
      expect(Commands.system(SystemCommand.lock), {
        'action': 'system_control',
        'command': 'lock',
      });
      expect(SystemCommand.shutdown.isDestructive, isTrue);
      expect(SystemCommand.restart.isDestructive, isTrue);
      expect(SystemCommand.lock.isDestructive, isFalse);
      expect(SystemCommand.explorer.isDestructive, isFalse);
    });
  });

  group('AuthPayloads', () {
    test('pairing and token payloads', () {
      expect(AuthPayloads.pair('123456', 'Android'), {
        'pin': '123456',
        'device_name': 'Android',
      });
      expect(AuthPayloads.token('abc'), {'token': 'abc'});
    });
  });
}
