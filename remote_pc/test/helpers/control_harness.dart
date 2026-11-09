import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/theme.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/settings/data/settings_repository.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';

import 'recording_connection.dart';

/// Providers needed by the control screens, backed by a recording connection.
class ControlHarness {
  ControlHarness({ConnectionStatus status = ConnectionStatus.ready})
    : connection = RecordingConnection(status: status);

  final RecordingConnection connection;

  Widget wrap(Widget child) {
    return MultiProvider(
      providers: [
        Provider<RemoteConnection>.value(value: connection),
        Provider<CommandSender>.value(value: connection),
        ChangeNotifierProvider<SettingsController>(
          create: (_) => SettingsController(SettingsRepository())..load(),
        ),
        Provider<HapticsService>(
          create: (context) =>
              HapticsService(context.read<SettingsController>()),
        ),
        ChangeNotifierProvider<KeyboardOverlayController>(
          create: (_) => KeyboardOverlayController(connection: connection),
        ),
      ],
      child: MaterialApp(
        theme: AppTheme.dark(),
        home: Scaffold(body: child),
      ),
    );
  }
}

/// Gives the test a tall phone-like surface so the screens do not overflow.
/// The test font (Ahem) is much wider than the real one, so screens with long
/// labels in a row need a wider [logicalWidth].
void usePhoneSurface(WidgetTester tester, {double logicalWidth = 400}) {
  tester.view.physicalSize = Size(logicalWidth * 3, 2600);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}
