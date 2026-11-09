import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/ui/ui_utils.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';
import 'package:remote_pc/features/settings/presentation/settings_strings.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  /// Forgets the current server (saved token included) and closes the session.
  Future<void> _disconnectCompletely(BuildContext context) async {
    final connection = context.read<ConnectionController>();
    final serverId = connection.current?.serverId;
    if (serverId != null) {
      await connection.forget(serverId);
    } else {
      await connection.disconnect();
    }

    if (context.mounted) {
      UiUtils.showSnackBar(
        context,
        SettingsStrings.sessionEnded,
        isSuccess: true,
        icon: Icons.logout,
      );
      Navigator.of(context).popUntil((route) => route.isFirst);
    }
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsController>();

    return Scaffold(
      backgroundColor: AppColors.black,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              SettingsStrings.title,
              style: TextStyle(
                color: AppColors.white,
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),
            _Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.speed, color: AppColors.blue),
                      const SizedBox(width: 12),
                      const Text(
                        SettingsStrings.mouseSensitivity,
                        style: TextStyle(color: AppColors.white, fontSize: 16),
                      ),
                      const Spacer(),
                      Text(
                        '${settings.sensitivity.toStringAsFixed(1)}x',
                        style: const TextStyle(
                          color: AppColors.blue,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Slider(
                    value: settings.sensitivity,
                    min: SettingsController.minSensitivity,
                    max: SettingsController.maxSensitivity,
                    divisions: 9,
                    label: settings.sensitivity.toStringAsFixed(1),
                    activeColor: AppColors.blue,
                    inactiveColor: AppColors.grey700,
                    onChanged: (value) => settings.sensitivity = value,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _Card(
              child: Row(
                children: [
                  const Icon(Icons.vibration, color: AppColors.blue),
                  const SizedBox(width: 12),
                  const Text(
                    SettingsStrings.vibration,
                    style: TextStyle(color: AppColors.white, fontSize: 16),
                  ),
                  const Spacer(),
                  Switch(
                    value: settings.vibrationEnabled,
                    onChanged: (value) => settings.vibrationEnabled = value,
                    activeThumbColor: AppColors.blue,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _disconnectCompletely(context),
                icon: const Icon(Icons.logout),
                label: const Text(SettingsStrings.disconnectCompletely),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.red.withValues(alpha: 0.2),
                  foregroundColor: AppColors.red,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const _Card(
              child: Column(
                children: [
                  ListTile(
                    leading: Icon(Icons.info_outline, color: AppColors.grey),
                    title: Text(
                      SettingsStrings.version,
                      style: TextStyle(color: AppColors.white),
                    ),
                    trailing: Text(
                      SettingsStrings.versionNumber,
                      style: TextStyle(color: AppColors.grey),
                    ),
                  ),
                  ListTile(
                    leading: Icon(Icons.code, color: AppColors.grey),
                    title: Text(
                      SettingsStrings.developer,
                      style: TextStyle(color: AppColors.white),
                    ),
                    trailing: Text(
                      SettingsStrings.developerName,
                      style: TextStyle(color: AppColors.grey),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.grey900,
        borderRadius: BorderRadius.circular(12),
      ),
      child: child,
    );
  }
}
