/// Explicit connection state. No loose booleans.
enum ConnectionStatus {
  idle,
  searching,
  connecting,
  authenticating,
  ready,
  reconnecting,
  error,
}
