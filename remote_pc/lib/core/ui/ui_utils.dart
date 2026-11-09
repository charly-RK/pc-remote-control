import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';

/// Shared SnackBar styling (same look as the original app).
class UiUtils {
  UiUtils._();

  static void showSnackBar(
    BuildContext context,
    String message, {
    Color? backgroundColor,
    IconData? icon,
    bool isError = false,
    bool isSuccess = false,
  }) {
    var bgColor = backgroundColor ?? AppColors.snackBar;
    var iconData = icon ?? Icons.info_outline;
    final iconColor = AppColors.white.withValues(alpha: 0.9);

    if (isError) {
      bgColor = AppColors.dangerDark.withValues(alpha: 0.9);
      iconData = Icons.error_outline;
    } else if (isSuccess) {
      bgColor = AppColors.successDark.withValues(alpha: 0.9);
      iconData = Icons.check_circle_outline;
    } else {
      bgColor = bgColor.withValues(alpha: 0.9);
    }

    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(iconData, color: iconColor, size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(
                  color: AppColors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                ),
              ),
            ),
          ],
        ),
        backgroundColor: bgColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        elevation: 2,
        duration: const Duration(seconds: 2),
      ),
    );
  }
}
