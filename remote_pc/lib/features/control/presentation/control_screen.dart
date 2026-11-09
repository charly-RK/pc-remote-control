import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/core/network/connection_status.dart';
import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';
import 'package:remote_pc/features/control/presentation/control_strings.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/media/presentation/media_screen.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';
import 'package:remote_pc/features/settings/presentation/settings_screen.dart';
import 'package:remote_pc/features/system/presentation/system_screen.dart';
import 'package:remote_pc/features/touchpad/presentation/touchpad_screen.dart';

/// Main screen while connected: compact status bar, the selected tab and the
/// bottom navigation. Scopes the control-session state (keyboard overlay,
/// haptics) so it lives while this screen is shown.
class ControlScreen extends StatelessWidget {
  const ControlScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<HapticsService>(
          create: (context) =>
              HapticsService(context.read<SettingsController>()),
        ),
        ChangeNotifierProvider<KeyboardOverlayController>(
          create: (context) => KeyboardOverlayController(
            connection: context.read<RemoteConnection>(),
          ),
        ),
      ],
      child: const _ControlView(),
    );
  }
}

class _ControlView extends StatefulWidget {
  const _ControlView();

  @override
  State<_ControlView> createState() => _ControlViewState();
}

class _ControlViewState extends State<_ControlView> {
  int _selectedIndex = 0;

  final List<Widget> _screens = const [
    TouchpadScreen(),
    MediaScreen(),
    SystemScreen(),
    SettingsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    // The original app gave a light haptic tick when authentication succeeded.
    context.read<HapticsService>().light();
  }

  @override
  Widget build(BuildContext context) {
    final status = context.watch<ConnectionController>().status;
    final isConnected = status == ConnectionStatus.ready;
    final isReconnecting =
        status == ConnectionStatus.reconnecting ||
        status == ConnectionStatus.connecting ||
        status == ConnectionStatus.authenticating;

    return Scaffold(
      backgroundColor: AppColors.black,
      body: Column(
        children: [
          SafeArea(
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 8.0,
                vertical: 5.0,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Flexible(
                    child: _StatusChip(
                      connected: isConnected,
                      reconnecting: isReconnecting,
                    ),
                  ),
                  if (isConnected || isReconnecting)
                    IconButton(
                      icon: const Icon(Icons.power_settings_new, size: 18),
                      color: AppColors.red,
                      onPressed: () =>
                          context.read<ConnectionController>().disconnect(),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                ],
              ),
            ),
          ),
          Container(height: 0.5, color: AppColors.grey800),
          Expanded(child: _screens[_selectedIndex]),
        ],
      ),
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  Widget _buildBottomNavigationBar() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.black,
        border: Border(top: BorderSide(color: AppColors.grey800, width: 0.5)),
      ),
      child: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) {
          if (index != _selectedIndex) {
            // The touchpad tab is rebuilt when we come back: close the keyboard
            // now so it does not reopen by itself.
            context.read<KeyboardOverlayController>().hide();
          }
          setState(() => _selectedIndex = index);
        },
        type: BottomNavigationBarType.fixed,
        backgroundColor: AppColors.transparent,
        selectedItemColor: AppColors.blue,
        unselectedItemColor: AppColors.grey600,
        selectedFontSize: 10,
        unselectedFontSize: 10,
        selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold),
        elevation: 0,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.mouse, size: 22),
            label: ControlStrings.mouse,
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.volume_up, size: 22),
            label: ControlStrings.media,
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.computer, size: 22),
            label: ControlStrings.system,
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings, size: 22),
            label: ControlStrings.settings,
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.connected, required this.reconnecting});

  final bool connected;
  final bool reconnecting;

  @override
  Widget build(BuildContext context) {
    final Color color = connected
        ? AppColors.green
        : (reconnecting ? AppColors.orange : AppColors.red);
    final String text = connected
        ? ControlStrings.connected
        : (reconnecting
              ? ControlStrings.reconnecting
              : ControlStrings.disconnected);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 2.0),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(12.0),
        border: Border.all(color: color, width: 1.0),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            connected ? Icons.circle : Icons.circle_outlined,
            size: 8,
            color: color,
          ),
          const SizedBox(width: 4),
          Flexible(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: color,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
