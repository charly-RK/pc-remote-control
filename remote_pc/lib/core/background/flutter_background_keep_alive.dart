import 'dart:async';
import 'dart:ui';

import 'package:flutter/foundation.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/background/background_keep_alive.dart';

const _channelId = 'my_foreground';
const _notificationId = 888;

/// [BackgroundKeepAlive] backed by flutter_background_service.
class FlutterBackgroundKeepAlive implements BackgroundKeepAlive {
  final FlutterBackgroundService _service = FlutterBackgroundService();

  @override
  Future<void> initialize() async {
    try {
      const channel = AndroidNotificationChannel(
        _channelId,
        'Control PC',
        description: 'Notificación de la sesión activa.',
        importance: Importance.high,
      );
      final notifications = FlutterLocalNotificationsPlugin();
      final android = notifications
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >();
      await android?.requestNotificationsPermission();
      await android?.createNotificationChannel(channel);

      await _service.configure(
        androidConfiguration: AndroidConfiguration(
          onStart: onBackgroundStart,
          autoStart: false,
          isForegroundMode: true,
          notificationChannelId: _channelId,
          initialNotificationTitle: 'Control PC',
          initialNotificationContent: 'Inicializando...',
          foregroundServiceNotificationId: _notificationId,
        ),
        iosConfiguration: IosConfiguration(
          autoStart: false,
          onForeground: onBackgroundStart,
          onBackground: onIosBackground,
        ),
      );
    } on Object catch (error) {
      debugPrint('Background service unavailable: $error');
    }
  }

  @override
  Future<void> start(String content) async {
    try {
      if (!await _service.isRunning()) {
        await _service.startService();
      }
      _service.invoke('updateNotification', {'content': content});
    } on Object catch (error) {
      debugPrint('Background service start failed: $error');
    }
  }

  @override
  Future<void> stop() async {
    try {
      _service.invoke('stopService');
    } on Object catch (error) {
      debugPrint('Background service stop failed: $error');
    }
  }
}

@pragma('vm:entry-point')
Future<bool> onIosBackground(ServiceInstance service) async => true;

@pragma('vm:entry-point')
void onBackgroundStart(ServiceInstance service) async {
  DartPluginRegistrant.ensureInitialized();
  final notifications = FlutterLocalNotificationsPlugin();

  service.on('stopService').listen((event) => service.stopSelf());

  service.on('updateNotification').listen((event) {
    final content = event?['content'] as String?;
    if (content == null) return;
    notifications.show(
      _notificationId,
      'Control PC activo',
      content,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _channelId,
          'Control PC',
          icon: '@mipmap/ic_launcher',
          ongoing: true,
          importance: Importance.high,
          priority: Priority.high,
          color: AppColors.blue,
          styleInformation: BigTextStyleInformation(
            '$content<br>La sesión sigue activa en segundo plano.',
            htmlFormatBigText: true,
            contentTitle: '<b>Control PC activo</b>',
            htmlFormatContentTitle: true,
            summaryText: 'Conectado',
          ),
        ),
      ),
    );
  });
}
