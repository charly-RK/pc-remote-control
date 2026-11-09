import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/hidden_text_bridge.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/keyboard/presentation/widgets/keyboard_options_sheet.dart';

/// Draggable round button that toggles the native keyboard.
class FloatingKeyboardButton extends StatefulWidget {
  const FloatingKeyboardButton({
    super.key,
    required this.bridge,
    required this.screenSize,
    required this.onKeyboardShown,
    this.size = defaultSize,
  });

  static const double defaultSize = 60.0;

  final HiddenTextBridge bridge;
  final Size screenSize;
  final VoidCallback onKeyboardShown;
  final double size;

  /// Keeps the button inside the screen.
  static double clampPosition(
    double position,
    double buttonSize,
    double screenSize,
  ) {
    return position.clamp(0.0, screenSize - buttonSize);
  }

  @override
  State<FloatingKeyboardButton> createState() => _FloatingKeyboardButtonState();
}

class _FloatingKeyboardButtonState extends State<FloatingKeyboardButton> {
  bool _isDragging = false;

  @override
  Widget build(BuildContext context) {
    final overlay = context.watch<KeyboardOverlayController>();
    final size = widget.size;
    final shown = overlay.showNativeKeyboard;

    return GestureDetector(
      onPanStart: (_) => setState(() => _isDragging = true),
      onPanUpdate: (details) {
        final next = overlay.keyboardButtonPosition.translate(
          details.delta.dx,
          details.delta.dy,
        );
        overlay.keyboardButtonPosition = Offset(
          FloatingKeyboardButton.clampPosition(
            next.dx,
            size,
            widget.screenSize.width,
          ),
          FloatingKeyboardButton.clampPosition(
            next.dy,
            size,
            widget.screenSize.height,
          ),
        );
      },
      onPanEnd: (_) => setState(() => _isDragging = false),
      onTap: () {
        if (_isDragging) return;
        overlay.toggle();
        if (overlay.showNativeKeyboard) {
          widget.onKeyboardShown();
          // Small delay so the invisible field is already built.
          Future<void>.delayed(const Duration(milliseconds: 100), () {
            if (context.mounted) {
              FocusScope.of(context).requestFocus(widget.bridge.focusNode);
            }
          });
        } else {
          widget.bridge.focusNode.unfocus();
        }
      },
      onLongPress: () => showKeyboardOptionsSheet(
        context,
        bridge: widget.bridge,
        buttonSize: size,
      ),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: shown ? AppColors.blue : AppColors.grey800,
          borderRadius: BorderRadius.circular(size / 2),
          border: Border.all(
            color: _isDragging ? AppColors.orange : AppColors.grey700,
            width: _isDragging ? 3 : 2,
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.black.withValues(alpha: 0.3),
              blurRadius: 10,
              spreadRadius: 2,
            ),
            BoxShadow(
              color: shown
                  ? AppColors.blue.withValues(alpha: 0.3)
                  : AppColors.grey600.withValues(alpha: 0.2),
              blurRadius: 5,
              spreadRadius: 1,
            ),
          ],
        ),
        child: Stack(
          children: [
            Center(
              child: Icon(
                shown ? Icons.keyboard_hide : Icons.keyboard,
                color: AppColors.white,
                size: 30,
              ),
            ),
            if (_isDragging)
              Positioned(
                top: 5,
                right: 5,
                child: Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: AppColors.orange,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Icon(
                    Icons.open_with,
                    size: 8,
                    color: AppColors.white,
                  ),
                ),
              ),
            if (shown && !_isDragging)
              Positioned(
                top: 5,
                right: 5,
                child: Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    color: AppColors.green,
                    borderRadius: BorderRadius.circular(5),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
