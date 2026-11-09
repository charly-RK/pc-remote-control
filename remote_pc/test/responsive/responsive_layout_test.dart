import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/features/connection/presentation/pages/connection_screen.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/features/control/presentation/control_screen.dart';
import 'package:remote_pc/features/keyboard/presentation/widgets/floating_keyboard_button.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/real_font.dart';
import '../helpers/recording_connection.dart';
import '../helpers/test_app.dart';

/// Real device sizes (logical pixels). A layout that overflows at any of them
/// shows the red overflow error in the app, so these tests must stay green.
const _sizes = <String, Size>{
  'small phone 320x568': Size(320, 568),
  'phone 360x800': Size(360, 800),
  'large phone 412x915': Size(412, 915),
  'tablet portrait 768x1024': Size(768, 1024),
  'tablet landscape 1024x768': Size(1024, 768),
};

void _useSize(WidgetTester tester, Size size) {
  tester.view.physicalSize = size * 2;
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

  ThemeData theme() => appThemeWith(realFont: realFont);

  for (final entry in _sizes.entries) {
    group(entry.key, () {
      testWidgets('ConnectionScreen has no overflow', (tester) async {
        _useSize(tester, entry.value);
        final app = TestApp();
        await tester.pumpWidget(
          app.wrap(const ConnectionScreen(), theme: theme()),
        );
        await tester.pump();
        expect(tester.takeException(), isNull);
      });

      testWidgets('ControlScreen tabs have no overflow', (tester) async {
        _useSize(tester, entry.value);
        final app = TestApp();
        await tester.pumpWidget(
          app.wrap(const ControlScreen(), theme: theme()),
        );
        await tester.pump();
        expect(tester.takeException(), isNull, reason: 'touchpad tab');

        for (final tab in ['Multimedia', 'Sistema', 'Configuración']) {
          await tester.tap(find.text(tab));
          await tester.pump();
          expect(tester.takeException(), isNull, reason: '$tab tab');
        }
      });

      testWidgets('touchpad with the keyboard open has no overflow', (
        tester,
      ) async {
        _useSize(tester, entry.value);
        final app = TestApp();
        await app.connection.pair(
          const ServerEndpoint('10.0.0.5', 5723),
          '123456',
          'Test',
        );
        await tester.pumpWidget(
          app.wrap(const ControlScreen(), theme: theme()),
        );
        await tester.pump();
        await tester.tap(find.byType(FloatingKeyboardButton));
        await tester.pump(const Duration(milliseconds: 300));
        expect(tester.takeException(), isNull);
      });
    });
  }
}
