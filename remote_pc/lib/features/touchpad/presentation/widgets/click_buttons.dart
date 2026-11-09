import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/features/touchpad/presentation/controllers/touchpad_controller.dart';
import 'package:remote_pc/features/touchpad/presentation/touchpad_strings.dart';

/// Bottom bar with the left, middle and right click buttons.
/// Must be placed inside a [Stack].
class TouchpadClickButtons extends StatelessWidget {
  const TouchpadClickButtons({super.key, required this.controller});

  final TouchpadController controller;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: 0,
      right: 0,
      bottom: 0,
      child: Container(
        height: 80,
        decoration: BoxDecoration(
          color: AppColors.grey850,
          borderRadius: const BorderRadius.only(
            bottomLeft: Radius.circular(16),
            bottomRight: Radius.circular(16),
          ),
          border: Border(top: BorderSide(color: AppColors.grey700, width: 1.5)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _ClickButton(
              icon: Icons.mouse,
              color: AppColors.blue,
              label: TouchpadStrings.leftClick,
              onTap: controller.leftClick,
              onLongPress: controller.doubleClick,
            ),
            _ClickButton(
              icon: Icons.adjust,
              color: AppColors.grey,
              label: TouchpadStrings.middleClick,
              onTap: controller.middleClick,
            ),
            _ClickButton(
              icon: Icons.mouse,
              color: AppColors.red,
              label: TouchpadStrings.rightClick,
              onTap: controller.rightClick,
            ),
          ],
        ),
      ),
    );
  }
}

class _ClickButton extends StatelessWidget {
  const _ClickButton({
    required this.icon,
    required this.color,
    required this.label,
    required this.onTap,
    this.onLongPress,
  });

  final IconData icon;
  final Color color;
  final String label;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        onLongPress: onLongPress,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color.withValues(alpha: 0.3), width: 1),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 20, color: color),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  color: color,
                  fontSize: 10,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
