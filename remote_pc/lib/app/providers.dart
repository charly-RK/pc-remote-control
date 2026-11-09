import 'dart:io';

import 'package:provider/provider.dart';
import 'package:provider/single_child_widget.dart';
import 'package:remote_pc/core/background/background_keep_alive.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/network/discovery_service.dart';
import 'package:remote_pc/core/network/nsd_discovery_service.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/network/socket_io_connection.dart';
import 'package:remote_pc/core/storage/server_store.dart';
import 'package:remote_pc/features/connection/data/legacy_connection_source.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/settings/data/settings_repository.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';

/// Composition root of the app: the only place that creates concrete
/// implementations and exposes them through Provider.
List<SingleChildWidget> buildProviders({
  required BackgroundKeepAlive keepAlive,
}) {
  final connection = SocketIoConnection();
  final DiscoveryService discovery = NsdDiscoveryService();
  final ServerStore store = PersistentServerStore();

  return [
    Provider<RemoteConnection>.value(value: connection),
    Provider<CommandSender>.value(value: connection),
    Provider<DiscoveryService>.value(value: discovery),
    ChangeNotifierProvider<ConnectionController>(
      create: (_) => ConnectionController(
        connection: connection,
        discovery: discovery,
        store: store,
        deviceName: _deviceName(),
        keepAlive: keepAlive,
        legacySource: PrefsLegacyConnectionSource(),
      ),
    ),
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
}

String _deviceName() {
  if (Platform.isAndroid) return 'Android';
  if (Platform.isIOS) return 'iOS';
  return 'Teléfono';
}
