/// What the control features need from the connection. Features depend on this
/// interface only, never on the socket implementation.
library;

class CommandResponse {
  const CommandResponse({required this.ok, this.code, this.message, this.data});

  final bool ok;
  final String? code;
  final String? message;

  /// Optional structured payload of the response (for example the media state).
  final Map<String, dynamic>? data;

  static const notReady = CommandResponse(
    ok: false,
    code: 'NOT_CONNECTED',
    message: 'Not connected',
  );
}

abstract class CommandSender {
  /// True when the connection is authenticated and commands can be sent.
  bool get isReady;

  /// Fire-and-forget for high-frequency input (mouse movement). Dropped silently
  /// when not ready. The server sends no acknowledgement for these commands.
  void fire(Map<String, dynamic> payload);

  /// Sends a command and waits for the server acknowledgement.
  Future<CommandResponse> request(Map<String, dynamic> payload);
}
