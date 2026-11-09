import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/features/settings/data/settings_repository.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';
import 'package:remote_pc/features/touchpad/presentation/controllers/touchpad_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/fake_command_sender.dart';
import '../helpers/recording_connection.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late FakeCommandSender sender;
  late SettingsController settings;
  late DateTime now;
  late TouchpadController pad;
  late List<String> haptic;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    haptic = mockHaptics(
      TestWidgetsFlutterBinding.instance.defaultBinaryMessenger,
    );
    sender = FakeCommandSender();
    settings = SettingsController(SettingsRepository());
    now = DateTime(2026, 1, 1, 12);
    pad = TouchpadController(
      sender: sender,
      settings: settings,
      haptics: HapticsService(settings),
      clock: () => now,
    );
  });

  tearDown(() => pad.dispose());

  test(
    'cursor movement is throttled to one send every 16 ms and accumulates',
    () {
      pad.panStart(Offset.zero);

      now = now.add(const Duration(milliseconds: 10));
      pad.panUpdate(const Offset(10, 5)); // default sensitivity is 2.0
      expect(sender.fired, isEmpty);

      now = now.add(const Duration(milliseconds: 40));
      pad.panUpdate(const Offset(20, 10));
      expect(sender.fired, [
        {'action': 'mouse_move', 'x': 40, 'y': 20},
      ]);
    },
  );

  test('sends on every 60 Hz frame (16 ms boundary included)', () {
    pad.panStart(Offset.zero);
    for (var i = 1; i <= 5; i++) {
      now = now.add(const Duration(milliseconds: 16));
      pad.panUpdate(Offset(i * 5.0, 0)); // 10 px per frame at sensitivity 2.0
    }
    expect(sender.fired.length, 5);
    expect(sender.fired.every((p) => p['x'] == 10), isTrue);
  });

  test('sub-pixel remainders are kept for the next send', () async {
    settings.sensitivity = 0.5;
    pad.panStart(Offset.zero);

    now = now.add(const Duration(milliseconds: 40));
    pad.panUpdate(const Offset(3, 0)); // 1.5 -> sends 1, keeps 0.5
    expect(sender.fired.single['x'], 1);

    now = now.add(const Duration(milliseconds: 40));
    pad.panUpdate(const Offset(5, 0)); // +1.0 -> 1.5 -> sends 1
    expect(sender.fired.last['x'], 1);
  });

  test('moving without a pan start sends nothing', () {
    now = now.add(const Duration(milliseconds: 100));
    pad.panUpdate(const Offset(50, 50));
    expect(sender.fired, isEmpty);
  });

  test('pan state is exposed for the UI', () {
    pad.panStart(Offset.zero);
    expect(pad.isDragging, isTrue);
    pad.panEnd();
    expect(pad.isDragging, isFalse);
  });

  test('click buttons send the original payloads', () {
    pad.leftClick();
    pad.doubleClick();
    pad.middleClick();
    pad.rightClick();
    expect(sender.fired, [
      {'action': 'mouse_click', 'button': 'left', 'type': 'single'},
      {'action': 'mouse_click', 'button': 'left', 'type': 'double'},
      {'action': 'mouse_click', 'button': 'middle', 'type': 'single'},
      {'action': 'mouse_click', 'button': 'right', 'type': 'single'},
    ]);
  });

  test('scroll bar multiplies the drag by two and throttles', () {
    pad.scrollBarStart();
    pad.scrollBarUpdate(10);
    expect(sender.fired, isEmpty);

    now = now.add(const Duration(milliseconds: 40));
    pad.scrollBarUpdate(10);
    expect(sender.fired.single['action'], 'mouse_scroll');
    expect(sender.fired.single['dy'], 40);
  });

  test('shortcuts send the key with the Ctrl modifier', () {
    pad.shortcut('c', ctrl: true);
    expect(sender.fired.single, {
      'action': 'key_press',
      'key': 'c',
      'ctrl': true,
    });
  });

  testWidgets('continuous scroll repeats every 100 ms until stopped', (
    tester,
  ) async {
    pad.startContinuousScroll(up: true);
    expect(pad.continuousScrolling, isTrue);
    expect(pad.isScrollingUp, isTrue);
    expect(sender.fired.single['dy'], 100);

    await tester.pump(const Duration(milliseconds: 100));
    expect(sender.fired.last['dy'], 50);
    await tester.pump(const Duration(milliseconds: 100));
    expect(sender.fired.length, 3);

    pad.stopContinuousScroll();
    expect(pad.continuousScrolling, isFalse);
    await tester.pump(const Duration(milliseconds: 300));
    expect(sender.fired.length, 3);
  });

  testWidgets('continuous scroll down uses negative steps', (tester) async {
    pad.startContinuousScroll(up: false);
    await tester.pump(const Duration(milliseconds: 100));
    expect(sender.fired.map((p) => p['dy']), [-100, -50]);
    pad.stopContinuousScroll();
  });

  test('vibration is skipped when disabled in settings', () async {
    settings.vibrationEnabled = false;
    pad.leftClick();
    await Future<void>.delayed(Duration.zero);
    expect(haptic, isEmpty);
  });

  test('taps vibrate lightly when enabled', () async {
    pad.leftClick();
    await Future<void>.delayed(Duration.zero);
    expect(haptic, ['HapticFeedbackType.lightImpact']);
  });
}
