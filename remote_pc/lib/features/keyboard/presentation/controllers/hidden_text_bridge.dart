import 'package:flutter/widgets.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';

/// Turns edits of an invisible text field into key presses and typed text.
///
/// The field always holds a small buffer of zero-width characters so that the
/// native keyboard can delete even when nothing was typed.
class HiddenTextBridge {
  HiddenTextBridge(this._sender) {
    _previousText = buffer;
    controller.text = buffer;
    controller.addListener(_onChanged);
  }

  static const String buffer = '\u200b\u200b\u200b';

  final CommandSender _sender;
  final TextEditingController controller = TextEditingController();
  final FocusNode focusNode = FocusNode();
  String _previousText = '';
  bool _disposed = false;
  bool _restoreScheduled = false;

  void _onChanged() {
    final currentText = controller.text;

    // Avoid a feedback loop when the buffer itself is restored.
    if (currentText == buffer) {
      _previousText = currentText;
      return;
    }

    if (currentText.length < _previousText.length) {
      final diff = _previousText.length - currentText.length;
      for (var i = 0; i < diff; i++) {
        _sender.fire(Commands.key('backspace'));
      }
    } else if (currentText.length > _previousText.length) {
      final newChars = currentText.replaceAll('\u200b', '');
      if (newChars.isNotEmpty) {
        _sender.fire(Commands.text(newChars));
      }
    }

    // Restore the buffer after the frame to allow continuous typing/deleting.
    // Several edits in one frame schedule a single restore.
    if (_restoreScheduled) return;
    _restoreScheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _restoreScheduled = false;
      if (_disposed) return;
      if (controller.text != buffer) {
        controller.text = buffer;
        controller.selection = const TextSelection.collapsed(offset: 3);
        _previousText = buffer;
      }
    });
    // addPostFrameCallback does not schedule a frame by itself.
    WidgetsBinding.instance.ensureVisualUpdate();
  }

  void submit() => _sender.fire(Commands.key('enter'));

  void clear() => controller.clear();

  void dispose() {
    _disposed = true;
    controller.dispose();
    focusNode.dispose();
  }
}
