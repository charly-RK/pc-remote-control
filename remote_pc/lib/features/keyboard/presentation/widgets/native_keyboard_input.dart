import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/hidden_text_bridge.dart';
import 'package:remote_pc/features/keyboard/presentation/keyboard_strings.dart';

/// Quick keys (Esc, F11, Start) and the invisible field that captures the
/// native keyboard input.
class NativeKeyboardInput extends StatelessWidget {
  const NativeKeyboardInput({
    super.key,
    required this.bridge,
    required this.sender,
    required this.haptics,
  });

  final HiddenTextBridge bridge;
  final CommandSender sender;
  final HapticsService haptics;

  void _quickKey(String key) {
    sender.fire(Commands.key(key));
    haptics.light();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.grey900,
        border: Border(top: BorderSide(color: AppColors.grey800, width: 1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 12.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _QuickKeyButton(
                  icon: Icons.cancel_presentation,
                  label: KeyboardStrings.escape,
                  onPressed: () => _quickKey('escape'),
                ),
                _QuickKeyButton(
                  icon: Icons.fullscreen,
                  label: KeyboardStrings.f11,
                  onPressed: () => _quickKey('f11'),
                ),
                _QuickKeyButton(
                  icon: Icons.window,
                  label: KeyboardStrings.home,
                  onPressed: () => _quickKey('win'),
                ),
              ],
            ),
          ),
          SizedBox(
            height: 1,
            width: 1,
            child: TextField(
              controller: bridge.controller,
              focusNode: bridge.focusNode,
              autofocus: true,
              decoration: const InputDecoration(
                border: InputBorder.none,
                contentPadding: EdgeInsets.zero,
              ),
              style: const TextStyle(color: AppColors.transparent, fontSize: 1),
              cursorColor: AppColors.transparent,
              maxLines: 1,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => bridge.submit(),
              enableSuggestions: false,
              autocorrect: false,
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickKeyButton extends StatelessWidget {
  const _QuickKeyButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.grey800,
        foregroundColor: AppColors.white,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(color: AppColors.grey700),
        ),
      ),
    );
  }
}
