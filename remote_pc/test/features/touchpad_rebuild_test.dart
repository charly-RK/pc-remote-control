import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/features/keyboard/presentation/widgets/floating_keyboard_button.dart';
import 'package:remote_pc/features/touchpad/presentation/touchpad_screen.dart';
import 'package:remote_pc/features/touchpad/presentation/widgets/touchpad_area.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/recording_connection.dart';
import '../helpers/test_app.dart';
import 'package:remote_pc/core/network/remote_connection.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    mockHaptics(TestWidgetsFlutterBinding.instance.defaultBinaryMessenger);
  });

  testWidgets(
    'the touch surface is not rebuilt while the keyboard insets animate',
    (tester) async {
      tester.view.physicalSize = const Size(360 * 2, 800 * 2);
      tester.view.devicePixelRatio = 2;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.view.resetViewInsets);

      final app = TestApp();
      await app.connection.pair(
        const ServerEndpoint('10.0.0.5', 5723),
        '123456',
        'Test',
      );
      await tester.pumpWidget(app.wrap(const TouchpadScreen()));
      await tester.pump();

      // Rebuilds of the surface show up as new element builds of TouchpadArea.
      final areaElement = tester.element(find.byType(TouchpadArea));
      final before = areaElement.widget;

      // Simulate the soft keyboard animation: the bottom inset changes per frame.
      for (var i = 1; i <= 12; i++) {
        tester.view.viewInsets = FakeViewPadding(bottom: i * 40.0);
        await tester.pump(const Duration(milliseconds: 16));
      }

      expect(tester.element(find.byType(TouchpadArea)), same(areaElement));
      expect(
        identical(tester.widget(find.byType(TouchpadArea)), before),
        isTrue,
        reason:
            'the same TouchpadArea instance must be reused, not recreated per frame',
      );
    },
  );

  testWidgets(
    'dragging the keyboard button does not recreate the touch surface',
    (tester) async {
      tester.view.physicalSize = const Size(360 * 2, 800 * 2);
      tester.view.devicePixelRatio = 2;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final app = TestApp();
      await app.connection.pair(
        const ServerEndpoint('10.0.0.5', 5723),
        '123456',
        'Test',
      );
      await tester.pumpWidget(app.wrap(const TouchpadScreen()));
      await tester.pump();

      final before = tester.widget(find.byType(TouchpadArea));
      await tester.drag(
        find.byType(FloatingKeyboardButton),
        const Offset(40, 120),
      );
      await tester.pump();
      expect(
        identical(tester.widget(find.byType(TouchpadArea)), before),
        isTrue,
      );
    },
  );
}
