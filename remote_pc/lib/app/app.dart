import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:provider/single_child_widget.dart';
import 'package:remote_pc/app/providers.dart';
import 'package:remote_pc/app/theme.dart';
import 'package:remote_pc/core/background/background_keep_alive.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';
import 'package:remote_pc/features/connection/presentation/pages/connection_screen.dart';
import 'package:remote_pc/features/control/presentation/control_screen.dart';

class RemoteApp extends StatelessWidget {
  const RemoteApp({
    super.key,
    this.keepAlive = const NoopBackgroundKeepAlive(),
    this.providers,
  });

  final BackgroundKeepAlive keepAlive;

  /// Replaces the production providers (used by tests).
  final List<SingleChildWidget>? providers;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: providers ?? buildProviders(keepAlive: keepAlive),
      child: MaterialApp(
        title: 'PC Remote Control',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.dark(),
        home: const AppWrapper(),
      ),
    );
  }
}

/// Shows the control screens once authenticated, the connection screen
/// otherwise. Starts the connection flow and reacts to the app lifecycle.
class AppWrapper extends StatefulWidget {
  const AppWrapper({super.key});

  @override
  State<AppWrapper> createState() => _AppWrapperState();
}

class _AppWrapperState extends State<AppWrapper> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) unawaited(context.read<ConnectionController>().start());
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      context.read<ConnectionController>().onResumed();
    }
  }

  @override
  Widget build(BuildContext context) {
    final authenticated = context.select<ConnectionController, bool>(
      (c) => c.isAuthenticated,
    );
    return authenticated ? const ControlScreen() : const ConnectionScreen();
  }
}
