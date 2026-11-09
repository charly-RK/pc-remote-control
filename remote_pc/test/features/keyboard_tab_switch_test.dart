import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/features/control/presentation/control_screen.dart';
import 'package:remote_pc/features/control/presentation/control_strings.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/keyboard/presentation/widgets/floating_keyboard_button.dart';
import 'package:remote_pc/features/keyboard/presentation/widgets/native_keyboard_input.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/real_font.dart';
import '../helpers/recording_connection.dart';
import '../helpers/test_app.dart';

void _phone(WidgetTester tester) {
  tester.view.physicalSize = const Size(360 * 2, 800 * 2);
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late bool realFont;

  setUpAll(() async {
    realFont = await loadRoboto();
  });

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    mockHaptics(TestWidgetsFlutterBinding.instance.defaultBinaryMessenger);
  });

  testWidgets(
    'the floating keyboard button starts docked at the top-left edge',
    (tester) async {
      _phone(tester);
      final app = TestApp();
      await app.connection.pair(
        const ServerEndpoint('10.0.0.5', 5723),
        '123456',
        'Test',
      );
      await tester.pumpWidget(
        app.wrap(
          const ControlScreen(),
          theme: appThemeWith(realFont: realFont),
        ),
      );
      await tester.pump();

      final topLeft = tester.getTopLeft(find.byType(FloatingKeyboardButton));
      final screen = tester.view.physicalSize / tester.view.devicePixelRatio;
      expect(topLeft.dx, lessThan(24), reason: 'must hug the left edge');
      expect(
        topLeft.dy,
        lessThan(screen.height * 0.25),
        reason: 'must not sit in the middle',
      );
      expect(
        KeyboardOverlayController.defaultButtonPosition,
        const Offset(4, 8),
      );
    },
  );

  testWidgets(
    'the keyboard closes when leaving the touchpad tab and stays closed on return',
    (tester) async {
      _phone(tester);
      final app = TestApp();
      await app.connection.pair(
        const ServerEndpoint('10.0.0.5', 5723),
        '123456',
        'Test',
      );
      await tester.pumpWidget(
        app.wrap(
          const ControlScreen(),
          theme: appThemeWith(realFont: realFont),
        ),
      );
      await tester.pump();

      await tester.tap(find.byType(FloatingKeyboardButton));
      await tester.pump(const Duration(milliseconds: 300));
      expect(find.byType(NativeKeyboardInput), findsOneWidget);

      await tester.tap(find.text(ControlStrings.media));
      await tester.pump();
      expect(find.byType(NativeKeyboardInput), findsNothing);

      await tester.tap(find.text(ControlStrings.mouse));
      await tester.pump(const Duration(milliseconds: 300));
      expect(
        find.byType(NativeKeyboardInput),
        findsNothing,
        reason: 'the keyboard must not reopen by itself',
      );
    },
  );
}
