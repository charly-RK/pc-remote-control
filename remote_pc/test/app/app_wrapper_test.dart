import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/app/app.dart';
import 'package:remote_pc/features/connection/domain/manual_input.dart';
import 'package:remote_pc/features/connection/presentation/pages/connection_screen.dart';
import 'package:remote_pc/features/control/presentation/control_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/test_app.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('AppWrapper switches between connection and control screens', (
    tester,
  ) async {
    final app = TestApp();
    await tester.pumpWidget(RemoteApp(providers: app.providers));
    await tester.pumpAndSettle();

    expect(find.byType(ConnectionScreen), findsOneWidget);
    expect(find.byType(ControlScreen), findsNothing);

    await app.controller.pairManual(
      const ManualInput(host: '192.168.1.5', port: 5723, pin: '123456'),
    );
    await tester.pumpAndSettle();

    expect(find.byType(ControlScreen), findsOneWidget);
    expect(find.byType(ConnectionScreen), findsNothing);

    await app.controller.disconnect();
    await tester.pumpAndSettle();

    expect(find.byType(ConnectionScreen), findsOneWidget);
    expect(find.byType(AppWrapper), findsOneWidget);
  });
}
