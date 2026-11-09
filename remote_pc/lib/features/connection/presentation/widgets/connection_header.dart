import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/features/connection/presentation/connection_strings.dart';

/// Logo, title and subtitle of the connection screen.
class ConnectionHeader extends StatelessWidget {
  const ConnectionHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            color: AppColors.blue.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(60),
            border: Border.all(
              color: AppColors.blue.withValues(alpha: 0.3),
              width: 2,
            ),
          ),
          child: const Icon(Icons.computer, size: 60, color: AppColors.blue),
        ),
        const SizedBox(height: 32),
        const Text(
          ConnectionStrings.title,
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
            color: AppColors.white,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        const Text(
          ConnectionStrings.subtitle,
          style: TextStyle(color: AppColors.grey, fontSize: 16),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
