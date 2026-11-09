import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/features/system/presentation/controllers/system_controller.dart';
import 'package:remote_pc/features/system/presentation/system_strings.dart';

class SystemScreen extends StatefulWidget {
  const SystemScreen({super.key});

  @override
  State<SystemScreen> createState() => _SystemScreenState();
}

class _SystemScreenState extends State<SystemScreen> {
  late final SystemController _system;

  @override
  void initState() {
    super.initState();
    _system = SystemController(context.read<CommandSender>());
  }

  VoidCallback _plain(SystemCommand command) =>
      () => _system.run(command);

  VoidCallback _confirmed(SystemCommand command, String title, String message) {
    return () => _showConfirmationDialog(
      context,
      title,
      message,
      () => _system.run(command, confirmed: true),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.black,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              const Text(
                SystemStrings.title,
                style: TextStyle(
                  fontSize: 24,
                  color: AppColors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 30),
              Expanded(
                child: GridView.count(
                  crossAxisCount: 3,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 1.0,
                  children: [
                    _SystemButton(
                      icon: Icons.screenshot_monitor,
                      label: SystemStrings.capture,
                      color: AppColors.green,
                      onPressed: _plain(SystemCommand.capture),
                    ),
                    _SystemButton(
                      icon: Icons.folder_open,
                      label: SystemStrings.explorer,
                      color: AppColors.blue,
                      onPressed: _plain(SystemCommand.explorer),
                    ),
                    _SystemButton(
                      icon: Icons.task,
                      label: SystemStrings.taskManager,
                      color: AppColors.amber,
                      onPressed: _plain(SystemCommand.taskManager),
                    ),
                    _SystemButton(
                      icon: Icons.lock,
                      label: SystemStrings.lock,
                      color: AppColors.orange,
                      onPressed: _plain(SystemCommand.lock),
                    ),
                    _SystemButton(
                      icon: Icons.power_settings_new,
                      label: SystemStrings.shutdown,
                      color: AppColors.red,
                      onPressed: _confirmed(
                        SystemCommand.shutdown,
                        SystemStrings.shutdownTitle,
                        SystemStrings.shutdownMessage,
                      ),
                    ),
                    _SystemButton(
                      icon: Icons.restart_alt,
                      label: SystemStrings.restart,
                      color: AppColors.blue,
                      onPressed: _confirmed(
                        SystemCommand.restart,
                        SystemStrings.restartTitle,
                        SystemStrings.restartMessage,
                      ),
                    ),
                    _SystemButton(
                      icon: Icons.bedtime,
                      label: SystemStrings.sleep,
                      color: AppColors.purple,
                      onPressed: _confirmed(
                        SystemCommand.sleep,
                        SystemStrings.sleepTitle,
                        SystemStrings.sleepMessage,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showConfirmationDialog(
    BuildContext context,
    String title,
    String message,
    VoidCallback onConfirm,
  ) {
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.grey900,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(title, style: const TextStyle(color: AppColors.white)),
        content: Text(message, style: const TextStyle(color: AppColors.grey)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text(
              SystemStrings.cancel,
              style: TextStyle(color: Colors.white70),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              onConfirm();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.red,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            child: const Text(
              SystemStrings.confirm,
              style: TextStyle(color: AppColors.white),
            ),
          ),
        ],
      ),
    );
  }
}

class _SystemButton extends StatelessWidget {
  const _SystemButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: AppColors.grey900,
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: AppColors.grey800, width: 1),
      ),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 24, color: color),
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(
                color: AppColors.white,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}
