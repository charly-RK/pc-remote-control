import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/features/control/presentation/control_screen.dart';
import 'package:remote_pc/features/media/presentation/media_screen.dart';
import 'package:remote_pc/features/settings/presentation/settings_screen.dart';
import 'package:remote_pc/features/system/presentation/system_screen.dart';
import 'package:remote_pc/features/touchpad/presentation/touchpad_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/control_harness.dart';
import '../helpers/recording_connection.dart';
import '../helpers/test_app.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    mockHaptics(TestWidgetsFlutterBinding.instance.defaultBinaryMessenger);
  });

  group('MediaScreen', () {
    testWidgets('buttons send canonical media_control commands', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const MediaScreen()));

      await tester.tap(find.byIcon(Icons.play_arrow));
      await tester.tap(find.byIcon(Icons.skip_next));
      await tester.tap(find.byIcon(Icons.skip_previous));
      await tester.tap(find.byIcon(Icons.volume_down).first);
      await tester.tap(find.byIcon(Icons.volume_mute).first);
      await tester.tap(find.byIcon(Icons.mic_off));
      await tester.pump();

      // Commands that change the PC state are requests (they bring the fresh
      // state back); the initial get_state comes from the screen's refresh.
      expect(harness.connection.requested.map((p) => p['command']), [
        'get_state',
        'play_pause',
        'next',
        'previous',
        'volume_down',
        'mute',
      ]);
      expect(harness.connection.fired.map((p) => p['command']), ['mic_mute']);
      expect(
        [
          ...harness.connection.requested,
          ...harness.connection.fired,
        ].every((p) => p['action'] == 'media_control'),
        isTrue,
      );
    });

    testWidgets('the play button shows pause and the slider follows the PC', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      harness.connection.onRequest = (payload) => const CommandResponse(
        ok: true,
        data: {'volume': 0.8, 'muted': false, 'playing': false},
      );
      await tester.pumpWidget(harness.wrap(const MediaScreen()));
      await tester.pump();

      expect(tester.widget<Slider>(find.byType(Slider)).value, 0.8);
      expect(find.byIcon(Icons.play_arrow), findsOneWidget);

      await tester.tap(find.byIcon(Icons.play_arrow));
      await tester.pump();
      expect(
        find.byIcon(Icons.pause),
        findsOneWidget,
        reason: 'optimistic toggle',
      );
      expect(find.byIcon(Icons.play_arrow), findsNothing);
    });

    testWidgets('the volume slider sends set_volume with the level', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const MediaScreen()));

      await tester.drag(find.byType(Slider), const Offset(60, 0));
      await tester.pump();

      final sent = harness.connection.fired.where(
        (p) => p['command'] == 'set_volume',
      );
      expect(sent, isNotEmpty);
      final level = sent.last['level'] as double;
      expect(level, greaterThan(0.5));
      expect(level, lessThanOrEqualTo(1.0));
    });
  });

  group('SystemScreen', () {
    testWidgets('non destructive actions are sent immediately', (tester) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const SystemScreen()));

      await tester.tap(find.text('Bloquear'));
      await tester.tap(find.text('Explorador'));
      await tester.pump();

      expect(harness.connection.fired, [
        {'action': 'system_control', 'command': 'lock'},
        {'action': 'system_control', 'command': 'explorer'},
      ]);
    });

    testWidgets('shutdown asks for confirmation and can be cancelled', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const SystemScreen()));

      await tester.tap(find.text('Apagar'));
      await tester.pumpAndSettle();
      expect(find.text('Apagar PC'), findsOneWidget);
      expect(harness.connection.fired, isEmpty);

      await tester.tap(find.text('Cancelar'));
      await tester.pumpAndSettle();
      expect(find.text('Apagar PC'), findsNothing);
      expect(harness.connection.fired, isEmpty);
    });

    testWidgets('destructive actions are sent only after confirming', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const SystemScreen()));

      for (final label in ['Apagar', 'Reiniciar', 'Suspender']) {
        await tester.tap(find.text(label));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Confirmar'));
        await tester.pumpAndSettle();
      }

      expect(harness.connection.fired.map((p) => p['command']), [
        'shutdown',
        'restart',
        'sleep',
      ]);
    });
  });

  group('TouchpadScreen', () {
    testWidgets('click buttons send mouse_click payloads', (tester) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const TouchpadScreen()));

      await tester.tap(find.text('Izquierdo'));
      await tester.tap(find.text('Central'));
      await tester.tap(find.text('Derecho'));

      expect(harness.connection.fired, [
        {'action': 'mouse_click', 'button': 'left', 'type': 'single'},
        {'action': 'mouse_click', 'button': 'middle', 'type': 'single'},
        {'action': 'mouse_click', 'button': 'right', 'type': 'single'},
      ]);
    });

    testWidgets('long press on the left button sends a double click', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const TouchpadScreen()));

      await tester.longPress(find.text('Izquierdo'));
      await tester.pump();

      expect(harness.connection.fired.single, {
        'action': 'mouse_click',
        'button': 'left',
        'type': 'double',
      });
    });

    testWidgets('options panel expands and sends Ctrl shortcuts', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const TouchpadScreen()));

      expect(find.text('Acciones rápidas'), findsNothing);
      await tester.tap(find.text('Mostrar opciones'));
      await tester.pumpAndSettle();
      expect(find.text('Acciones rápidas'), findsOneWidget);
      expect(find.text('Ocultar opciones'), findsOneWidget);

      await tester.tap(find.text('Copiar'));
      expect(harness.connection.fired.single, {
        'action': 'key_press',
        'key': 'c',
        'ctrl': true,
      });
    });

    testWidgets('the floating button toggles the native keyboard quick keys', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const TouchpadScreen()));

      expect(find.text('Esc'), findsNothing);
      await tester.tap(find.byIcon(Icons.keyboard));
      await tester.pump(const Duration(milliseconds: 200));
      expect(find.text('Esc'), findsOneWidget);
      expect(find.byIcon(Icons.keyboard_hide), findsOneWidget);

      await tester.tap(find.text('Esc'));
      await tester.tap(find.text('Inicio'));
      expect(harness.connection.fired.map((p) => p['key']), ['escape', 'win']);

      await tester.tap(find.byIcon(Icons.keyboard_hide));
      await tester.pump(const Duration(milliseconds: 200));
      expect(find.text('Esc'), findsNothing);
    });

    testWidgets(
      'long press on the floating button opens the keyboard options',
      (tester) async {
        usePhoneSurface(tester);
        final harness = ControlHarness();
        await tester.pumpWidget(harness.wrap(const TouchpadScreen()));

        await tester.longPress(find.byIcon(Icons.keyboard));
        await tester.pumpAndSettle();
        expect(find.text('Opciones del Teclado'), findsOneWidget);
        expect(find.text('Centrar Botón'), findsOneWidget);

        await tester.tap(find.text('Cerrar'));
        await tester.pumpAndSettle();
        expect(find.text('Opciones del Teclado'), findsNothing);
      },
    );

    testWidgets('the floating button is hidden while disconnected', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness(status: ConnectionStatus.idle);
      await tester.pumpWidget(harness.wrap(const TouchpadScreen()));
      expect(find.byIcon(Icons.keyboard), findsNothing);
    });

    testWidgets('scroll bar buttons start and stop continuous scrolling', (
      tester,
    ) async {
      usePhoneSurface(tester);
      final harness = ControlHarness();
      await tester.pumpWidget(harness.wrap(const TouchpadScreen()));

      final gesture = await tester.startGesture(
        tester.getCenter(find.byIcon(Icons.arrow_upward)),
      );
      await tester.pump(const Duration(milliseconds: 250));
      await gesture.up();
      await tester.pump();

      final scrolls = harness.connection.fired.where(
        (p) => p['action'] == 'mouse_scroll',
      );
      expect(scrolls.first['dy'], 100);
      expect(scrolls.length, greaterThanOrEqualTo(2));
      final countAfterStop = scrolls.length;
      await tester.pump(const Duration(milliseconds: 300));
      expect(
        harness.connection.fired
            .where((p) => p['action'] == 'mouse_scroll')
            .length,
        countAfterStop,
      );
    });
  });

  group('SettingsScreen', () {
    testWidgets('changing the switch persists with the original key', (
      tester,
    ) async {
      usePhoneSurface(tester, logicalWidth: 900);
      final app = TestApp();
      await tester.pumpWidget(app.wrap(const SettingsScreen()));
      await tester.pumpAndSettle();

      expect(find.text('Sensibilidad del Mouse'), findsOneWidget);
      await tester.tap(find.byType(Switch));
      await tester.pumpAndSettle();

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool('vibration'), isFalse);
    });

    testWidgets('disconnect completely ends the session', (tester) async {
      usePhoneSurface(tester, logicalWidth: 900);
      final app = TestApp();
      await tester.pumpWidget(app.wrap(const SettingsScreen()));

      await tester.tap(find.text('Desconectar Completamente'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(app.controller.status, ConnectionStatus.idle);
      expect(find.text('Sesión finalizada.'), findsOneWidget);
    });
  });

  group('ControlScreen', () {
    testWidgets('shows the status and switches tabs', (tester) async {
      usePhoneSurface(tester, logicalWidth: 900);
      final app = TestApp();
      await tester.pumpWidget(app.wrap(const ControlScreen()));
      await tester.pump();

      expect(find.text('Desconectado'), findsOneWidget);
      expect(find.byIcon(Icons.power_settings_new), findsNothing);
      expect(find.text('Desliza para mover el cursor'), findsOneWidget);

      await tester.tap(find.text('Multimedia'));
      await tester.pump();
      expect(find.text('Control Multimedia'), findsOneWidget);

      await tester.tap(find.text('Sistema'));
      await tester.pump();
      expect(find.text('Control de Sistema'), findsOneWidget);

      await tester.tap(find.text('Configuración'));
      await tester.pump();
      expect(find.text('Sensibilidad del Mouse'), findsOneWidget);
    });
  });
}
