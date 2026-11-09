import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/features/touchpad/presentation/controllers/touchpad_controller.dart';

/// Right-hand scroll strip: continuous scroll buttons and a draggable bar.
/// Must be placed inside a [Stack].
class TouchpadScrollBar extends StatelessWidget {
  const TouchpadScrollBar({super.key, required this.controller});

  final TouchpadController controller;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      right: 0,
      top: 0,
      bottom: 80,
      child: ListenableBuilder(
        listenable: controller,
        builder: (context, _) {
          final scrollingUp =
              controller.continuousScrolling && controller.isScrollingUp;
          final scrollingDown =
              controller.continuousScrolling && !controller.isScrollingUp;
          return Container(
            width: 60,
            decoration: BoxDecoration(
              borderRadius: const BorderRadius.only(
                topRight: Radius.circular(16),
              ),
              color: AppColors.black.withValues(alpha: 0.3),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _ScrollButton(
                  icon: Icons.arrow_upward,
                  active: scrollingUp,
                  topRightRounded: true,
                  onStart: () => controller.startContinuousScroll(up: true),
                  onStop: controller.stopContinuousScroll,
                ),
                Expanded(child: _ScrollTrack(controller: controller)),
                _ScrollButton(
                  icon: Icons.arrow_downward,
                  active: scrollingDown,
                  topRightRounded: false,
                  onStart: () => controller.startContinuousScroll(up: false),
                  onStop: controller.stopContinuousScroll,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ScrollButton extends StatelessWidget {
  const _ScrollButton({
    required this.icon,
    required this.active,
    required this.topRightRounded,
    required this.onStart,
    required this.onStop,
  });

  final IconData icon;
  final bool active;
  final bool topRightRounded;
  final VoidCallback onStart;
  final VoidCallback onStop;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => onStart(),
      onTapUp: (_) => onStop(),
      onTapCancel: onStop,
      child: Container(
        height: 50,
        width: 60,
        decoration: BoxDecoration(
          color: active
              ? AppColors.orange.withValues(alpha: 0.8)
              : AppColors.grey800,
          borderRadius: topRightRounded
              ? const BorderRadius.only(topRight: Radius.circular(16))
              : null,
        ),
        child: Icon(icon, color: AppColors.white, size: 30),
      ),
    );
  }
}

class _ScrollTrack extends StatelessWidget {
  const _ScrollTrack({required this.controller});

  final TouchpadController controller;

  @override
  Widget build(BuildContext context) {
    final dragging = controller.scrollDragging;
    return GestureDetector(
      onPanStart: (_) => controller.scrollBarStart(),
      onPanUpdate: (details) => controller.scrollBarUpdate(details.delta.dy),
      onPanEnd: (_) => controller.scrollBarEnd(),
      child: Container(
        decoration: BoxDecoration(
          color: dragging
              ? AppColors.orange.withValues(alpha: 0.3)
              : AppColors.grey800.withValues(alpha: 0.5),
        ),
        child: Center(
          child: Container(
            width: 30,
            height: 60,
            decoration: BoxDecoration(
              color: dragging ? AppColors.orange : AppColors.grey700,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              Icons.mouse,
              color: dragging ? AppColors.white : AppColors.grey400,
            ),
          ),
        ),
      ),
    );
  }
}
