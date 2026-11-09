import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:provider/single_child_widget.dart';
import 'package:remote_pc/app/theme.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/reconnect_policy.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/settings/data/settings_repository.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';

import 'fake_connection.dart';

/// Test double of the composition root: same providers as production with
/// fake network, discovery and storage.
class TestApp {
  TestApp() : connection = FakeConnection(), store = MemoryStore() {
    controller = ConnectionController(
      connection: connection,
      discovery: FakeDiscovery(),
      store: store,
      deviceName: 'Test',
      policy: ReconnectPolicy(steps: const [Duration.zero]),
      scanTimeout: Duration.zero,
      wait: (_) async {},
    );
  }

  final FakeConnection connection;
  final MemoryStore store;
  late final ConnectionController controller;

  List<SingleChildWidget> get providers => [
    Provider<RemoteConnection>.value(value: connection),
    Provider<CommandSender>.value(value: connection),
    ChangeNotifierProvider<ConnectionController>.value(value: controller),
    ChangeNotifierProvider<SettingsController>(
      create: (_) => SettingsController(SettingsRepository())..load(),
    ),
    ProxyProvider<SettingsController, HapticsService>(
      update: (_, settings, previous) => previous ?? HapticsService(settings),
    ),
    ChangeNotifierProvider<KeyboardOverlayController>(
      create: (_) => KeyboardOverlayController(connection: connection),
    ),
  ];

  Widget wrap(Widget home, {ThemeData? theme}) => MultiProvider(
    providers: providers,
    child: MaterialApp(theme: theme ?? AppTheme.dark(), home: home),
  );
}
