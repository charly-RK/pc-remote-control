/// Deterministic exponential backoff: 1s, 2s, 4s, 8s, 15s, then capped at 30s.
/// Call [reset] after a successful connection.
class ReconnectPolicy {
  ReconnectPolicy({List<Duration>? steps})
    : _steps =
          steps ??
          const [
            Duration(seconds: 1),
            Duration(seconds: 2),
            Duration(seconds: 4),
            Duration(seconds: 8),
            Duration(seconds: 15),
            Duration(seconds: 30),
          ];

  final List<Duration> _steps;
  int _attempt = 0;

  int get attempt => _attempt;

  /// Returns the delay for the next attempt and advances the counter.
  Duration next() {
    final index = _attempt < _steps.length ? _attempt : _steps.length - 1;
    _attempt++;
    return _steps[index];
  }

  void reset() => _attempt = 0;
}
