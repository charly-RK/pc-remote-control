import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';
import 'package:remote_pc/features/touchpad/presentation/controllers/touchpad_controller.dart';
import 'package:remote_pc/features/touchpad/presentation/touchpad_strings.dart';

/// Button that expands or collapses the options panel.
class OptionsToggle extends StatelessWidget {
  const OptionsToggle({super.key, required this.expanded, required this.onTap});

  final bool expanded;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.grey900,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.grey800),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                color: AppColors.blue,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                expanded
                    ? TouchpadStrings.hideOptions
                    : TouchpadStrings.showOptions,
                style: const TextStyle(color: AppColors.blue, fontSize: 14),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Animated panel with the sensitivity slider and the quick shortcuts.
class OptionsPanel extends StatelessWidget {
  const OptionsPanel({
    super.key,
    required this.expanded,
    required this.controller,
    required this.settings,
  });

  final bool expanded;
  final TouchpadController controller;
  final SettingsController settings;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      height: expanded ? MediaQuery.of(context).size.height * 0.3 : 0,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.grey900,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.grey800, width: 1),
      ),
      child: expanded
          ? SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _SensitivitySlider(settings: settings),
                  const SizedBox(height: 10),
                  const Text(
                    TouchpadStrings.quickActions,
                    style: TextStyle(
                      color: AppColors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  _ActionGrid(controller: controller),
                ],
              ),
            )
          : null,
    );
  }
}

class _SensitivitySlider extends StatelessWidget {
  const _SensitivitySlider({required this.settings});

  final SettingsController settings;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: settings,
      builder: (context, _) {
        final value = settings.sensitivity;
        return Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.grey850,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.speed, size: 16, color: AppColors.blue),
                  const SizedBox(width: 6),
                  const Text(
                    TouchpadStrings.sensitivity,
                    style: TextStyle(color: AppColors.white, fontSize: 12),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 6,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.blue.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: AppColors.blue.withValues(alpha: 0.3),
                      ),
                    ),
                    child: Text(
                      '${value.toStringAsFixed(1)}x',
                      style: const TextStyle(
                        color: AppColors.blue,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              Slider(
                value: value,
                min: SettingsController.minSensitivity,
                max: SettingsController.maxSensitivity,
                divisions: 9,
                label: value.toStringAsFixed(1),
                activeColor: AppColors.blue,
                inactiveColor: AppColors.grey700,
                onChanged: (v) => settings.sensitivity = v,
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ActionGrid extends StatelessWidget {
  const _ActionGrid({required this.controller});

  final TouchpadController controller;

  @override
  Widget build(BuildContext context) {
    final actions = <_Shortcut>[
      const _Shortcut(
        TouchpadStrings.copy,
        Icons.content_copy,
        AppColors.cyan,
        'c',
      ),
      const _Shortcut(
        TouchpadStrings.paste,
        Icons.content_paste,
        AppColors.cyan,
        'v',
      ),
      const _Shortcut(TouchpadStrings.cut, Icons.cut, AppColors.orange, 'x'),
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 4,
        mainAxisSpacing: 4,
        childAspectRatio: 1.6,
      ),
      itemCount: actions.length,
      itemBuilder: (context, index) {
        final action = actions[index];
        return _ShortcutButton(
          shortcut: action,
          onTap: () => controller.shortcut(action.key, ctrl: true),
        );
      },
    );
  }
}

class _Shortcut {
  const _Shortcut(this.label, this.icon, this.color, this.key);

  final String label;
  final IconData icon;
  final Color color;
  final String key;
}

class _ShortcutButton extends StatelessWidget {
  const _ShortcutButton({required this.shortcut, required this.onTap});

  final _Shortcut shortcut;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = shortcut.color;
    return Material(
      color: AppColors.transparent,
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color.withValues(alpha: 0.3)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(6),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(shortcut.icon, size: 18, color: color),
                const SizedBox(height: 3),
                Text(
                  shortcut.label,
                  style: TextStyle(
                    color: color,
                    fontSize: 10,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 1),
                Text(
                  'Ctrl+${shortcut.key.toUpperCase()}',
                  style: TextStyle(color: AppColors.grey500, fontSize: 8),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
