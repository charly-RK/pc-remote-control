import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/features/connection/domain/manual_input.dart';
import 'package:remote_pc/features/connection/presentation/connection_strings.dart';
import 'package:remote_pc/features/connection/presentation/pages/connection_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/test_app.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('shows the original fields and the connect button', (
    tester,
  ) async {
    final app = TestApp();
    await tester.pumpWidget(app.wrap(const ConnectionScreen()));

    expect(find.text(ConnectionStrings.title), findsOneWidget);
    expect(find.text(ConnectionStrings.subtitle), findsOneWidget);
    expect(find.text(ConnectionStrings.ipLabel), findsOneWidget);
    expect(find.text(ConnectionStrings.pinLabel), findsOneWidget);
    expect(find.text(ConnectionStrings.connectButton), findsOneWidget);
    expect(find.byTooltip(ConnectionStrings.scanQrTooltip), findsOneWidget);
    expect(find.byTooltip(ConnectionStrings.searchTooltip), findsOneWidget);
  });

  testWidgets('asks for IP and PIN when the form is empty', (tester) async {
    final app = TestApp();
    await tester.pumpWidget(app.wrap(const ConnectionScreen()));

    await tester.tap(find.text(ConnectionStrings.connectButton));
    await tester.pump();

    expect(find.text(ConnectionStrings.enterIpAndPin), findsOneWidget);
    expect(app.connection.attempts, isEmpty);
  });

  testWidgets('pairs with the entered IP and PIN', (tester) async {
    final app = TestApp();
    await tester.pumpWidget(app.wrap(const ConnectionScreen()));

    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), '192.168.1.10');
    await tester.enterText(fields.at(1), '123456');
    await tester.tap(find.text(ConnectionStrings.connectButton));
    await tester.pumpAndSettle();

    expect(app.controller.status, ConnectionStatus.ready);
    expect(app.connection.attempts.single.ip, '192.168.1.10');
    expect(app.connection.attempts.single.port, 5723);
    expect(find.text(ConnectionStrings.connectOk), findsOneWidget);
  });

  testWidgets('shows the server error for a wrong PIN', (tester) async {
    final app = TestApp();
    await tester.pumpWidget(app.wrap(const ConnectionScreen()));

    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), '192.168.1.10');
    await tester.enterText(fields.at(1), '000000');
    await tester.tap(find.text(ConnectionStrings.connectButton));
    await tester.pumpAndSettle();

    expect(find.text('PIN incorrecto'), findsOneWidget);
    expect(app.controller.status, ConnectionStatus.error);
  });

  testWidgets('prefills the last saved address', (tester) async {
    final app = TestApp();
    await app.controller.pairManual(
      const ManualInput(host: '192.168.1.5', port: 5723, pin: '123456'),
    );
    await tester.pumpWidget(app.wrap(const ConnectionScreen()));

    expect(find.text('192.168.1.5'), findsOneWidget);
  });
}
