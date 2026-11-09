import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';

/// Sends system commands. Destructive commands (shutdown, restart, sleep,
/// logout) are refused unless the caller confirms them with the user first.
class SystemController {
  SystemController(this._sender);

  final CommandSender _sender;

  /// Returns false when a destructive command was not confirmed.
  bool run(SystemCommand command, {bool confirmed = false}) {
    if (command.isDestructive && !confirmed) return false;
    _sender.fire(Commands.system(command));
    return true;
  }
}
