import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:remote_pc/app/app.dart';
import 'package:remote_pc/core/background/background_keep_alive.dart';
import 'package:remote_pc/core/background/flutter_background_keep_alive.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);

  final BackgroundKeepAlive keepAlive = FlutterBackgroundKeepAlive();
  await keepAlive.initialize();

  runApp(RemoteApp(keepAlive: keepAlive));
}
