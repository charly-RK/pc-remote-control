/// Keeps the app alive while a session is active (Android foreground
/// service). Implementations must tolerate platforms without support.
abstract class BackgroundKeepAlive {
  /// Prepares notification channels and the service. Call once at startup.
  Future<void> initialize();

  /// Starts the service (if needed) and shows [content] in the notification.
  Future<void> start(String content);

  Future<void> stop();
}

/// Used in tests and on platforms without a background service.
class NoopBackgroundKeepAlive implements BackgroundKeepAlive {
  const NoopBackgroundKeepAlive();

  @override
  Future<void> initialize() async {}

  @override
  Future<void> start(String content) async {}

  @override
  Future<void> stop() async {}
}
