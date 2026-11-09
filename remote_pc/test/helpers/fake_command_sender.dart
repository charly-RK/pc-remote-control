import 'package:remote_pc/core/network/command_sender.dart';

/// Captures every payload sent by a controller.
class FakeCommandSender implements CommandSender {
  FakeCommandSender({
    this.ready = true,
    this.response = const CommandResponse(ok: true),
  });

  bool ready;
  CommandResponse response;
  final List<Map<String, dynamic>> fired = [];
  final List<Map<String, dynamic>> requested = [];

  @override
  bool get isReady => ready;

  @override
  void fire(Map<String, dynamic> payload) {
    if (ready) fired.add(payload);
  }

  @override
  Future<CommandResponse> request(Map<String, dynamic> payload) async {
    if (!ready) return CommandResponse.notReady;
    requested.add(payload);
    return response;
  }

  List<Map<String, dynamic>> get all => [...fired, ...requested];
}
