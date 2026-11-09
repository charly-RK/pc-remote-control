import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/hidden_text_bridge.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/keyboard/presentation/keyboard_strings.dart';

/// Bottom sheet opened by a long press on the floating keyboard button.
void showKeyboardOptionsSheet(
  BuildContext context, {
  required HiddenTextBridge bridge,
  required double buttonSize,
}) {
  final overlay = context.read<KeyboardOverlayController>();
  final haptics = context.read<HapticsService>();

  showModalBottomSheet<void>(
    context: context,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (sheetContext) {
      return Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              KeyboardStrings.optionsTitle,
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            ListTile(
              leading: Icon(
                overlay.showNativeKeyboard
                    ? Icons.visibility_off
                    : Icons.visibility,
                color: AppColors.blue,
              ),
              title: Text(
                overlay.showNativeKeyboard
                    ? KeyboardStrings.hideKeyboard
                    : KeyboardStrings.showKeyboard,
                style: const TextStyle(fontSize: 16),
              ),
              onTap: () {
                Navigator.pop(sheetContext);
                overlay.toggle();
                if (overlay.showNativeKeyboard) {
                  FocusScope.of(context).requestFocus(bridge.focusNode);
                } else {
                  bridge.focusNode.unfocus();
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete, color: AppColors.red),
              title: const Text(
                KeyboardStrings.deleteText,
                style: TextStyle(fontSize: 16),
              ),
              onTap: () {
                Navigator.pop(sheetContext);
                overlay.deleteText();
                bridge.clear();
                haptics.medium();
              },
            ),
            ListTile(
              leading: const Icon(
                Icons.center_focus_strong,
                color: AppColors.green,
              ),
              title: const Text(
                KeyboardStrings.centerButton,
                style: TextStyle(fontSize: 16),
              ),
              onTap: () {
                Navigator.pop(sheetContext);
                final screenSize = MediaQuery.of(context).size;
                overlay.keyboardButtonPosition = Offset(
                  (screenSize.width - buttonSize) / 2,
                  (screenSize.height - buttonSize) / 2,
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.crop_square, color: AppColors.amber),
              title: const Text(
                KeyboardStrings.hideInCorner,
                style: TextStyle(fontSize: 16),
              ),
              onTap: () {
                Navigator.pop(sheetContext);
                final screenSize = MediaQuery.of(context).size;
                overlay.keyboardButtonPosition = Offset(
                  screenSize.width - buttonSize - 20,
                  20,
                );
              },
            ),
            const SizedBox(height: 10),
            Divider(color: AppColors.grey300),
            const SizedBox(height: 10),
            ElevatedButton(
              onPressed: () => Navigator.pop(sheetContext),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.grey200,
                foregroundColor: AppColors.black,
                minimumSize: const Size(double.infinity, 50),
              ),
              child: const Text(KeyboardStrings.close),
            ),
          ],
        ),
      );
    },
  );
}
