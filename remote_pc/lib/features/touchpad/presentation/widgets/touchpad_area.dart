import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/features/touchpad/presentation/controllers/touchpad_controller.dart';
import 'package:remote_pc/features/touchpad/presentation/touchpad_strings.dart';

/// Main touch surface: tap, double tap and swipe to move the cursor.
/// Must be placed inside a [Stack].
class TouchpadArea extends StatelessWidget {
  const TouchpadArea({super.key, required this.controller});

  final TouchpadController controller;

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      bottom: 80,
      child: ListenableBuilder(
        listenable: controller,
        builder: (context, _) {
          return GestureDetector(
            onTap: controller.leftClick,
            onDoubleTap: controller.doubleClick,
            onPanStart: (details) => controller.panStart(details.localPosition),
            onPanUpdate: (details) =>
                controller.panUpdate(details.localPosition),
            onPanEnd: (_) => controller.panEnd(),
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                border: controller.isDragging
                    ? Border.all(
                        color: AppColors.blue.withValues(alpha: 0.3),
                        width: 2,
                      )
                    : null,
              ),
              child: _TouchpadContent(isDragging: controller.isDragging),
            ),
          );
        },
      ),
    );
  }
}

class _TouchpadContent extends StatelessWidget {
  const _TouchpadContent({required this.isDragging});

  final bool isDragging;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: isDragging
          ? Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.mouse,
                  size: 50,
                  color: AppColors.blue.withValues(alpha: 0.7),
                ),
                const SizedBox(height: 10),
                Text(
                  TouchpadStrings.movingCursor,
                  style: TextStyle(
                    color: AppColors.blue.withValues(alpha: 0.7),
                    fontSize: 16,
                  ),
                ),
              ],
            )
          : Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.touch_app, size: 50, color: AppColors.grey600),
                const SizedBox(height: 10),
                Text(
                  TouchpadStrings.swipeHint,
                  style: TextStyle(color: AppColors.grey600, fontSize: 14),
                ),
                const SizedBox(height: 5),
              ],
            ),
    );
  }
}
