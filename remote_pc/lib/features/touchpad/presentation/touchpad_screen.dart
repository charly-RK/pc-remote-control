import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/hidden_text_bridge.dart';
import 'package:remote_pc/features/keyboard/presentation/controllers/keyboard_overlay_controller.dart';
import 'package:remote_pc/features/keyboard/presentation/widgets/floating_keyboard_button.dart';
import 'package:remote_pc/features/keyboard/presentation/widgets/native_keyboard_input.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';
import 'package:remote_pc/features/touchpad/presentation/controllers/touchpad_controller.dart';
import 'package:remote_pc/features/touchpad/presentation/widgets/click_buttons.dart';
import 'package:remote_pc/features/touchpad/presentation/widgets/options_panel.dart';
import 'package:remote_pc/features/touchpad/presentation/widgets/scroll_bar.dart';
import 'package:remote_pc/features/touchpad/presentation/widgets/touchpad_area.dart';

/// Mouse tab: touchpad, scroll bar, click buttons, options panel and the
/// native-keyboard overlay with its draggable button.
class TouchpadScreen extends StatefulWidget {
  const TouchpadScreen({super.key});

  @override
  State<TouchpadScreen> createState() => _TouchpadScreenState();
}

class _TouchpadScreenState extends State<TouchpadScreen> {
  late final TouchpadController _pad;
  late final HiddenTextBridge _bridge;
  bool _showOptions = false;

  @override
  void initState() {
    super.initState();
    final sender = context.read<CommandSender>();
    _pad = TouchpadController(
      sender: sender,
      settings: context.read<SettingsController>(),
      haptics: context.read<HapticsService>(),
    );
    _bridge = HiddenTextBridge(sender);
  }

  @override
  void dispose() {
    _pad.dispose();
    _bridge.dispose();
    super.dispose();
  }

  void _toggleOptions(KeyboardOverlayController overlay) {
    setState(() {
      _showOptions = !_showOptions;
      if (_showOptions) {
        overlay.hide();
        _bridge.focusNode.unfocus();
      }
    });
  }

  /// The touch surface never changes after creation (it listens to the pad
  /// controller itself), so the same widget instance is reused on every rebuild
  /// and Flutter skips it while the keyboard opens or the button is dragged.
  late final Widget _surface = RepaintBoundary(
    child: Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.grey900,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.grey800, width: 2),
      ),
      child: Stack(
        children: [
          TouchpadArea(controller: _pad),
          TouchpadScrollBar(controller: _pad),
          TouchpadClickButtons(controller: _pad),
        ],
      ),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final overlay = context.read<KeyboardOverlayController>();
    // Only the keyboard visibility matters here, not every overlay change.
    final showKeyboard = context.select<KeyboardOverlayController, bool>(
      (o) => o.showNativeKeyboard,
    );

    return GestureDetector(
      onTap: () {
        // Hide the keyboard when tapping outside of it.
        if (_bridge.focusNode.hasFocus) {
          _bridge.focusNode.unfocus();
        }
      },
      child: Scaffold(
        resizeToAvoidBottomInset: false,
        body: Stack(
          children: [
            Column(
              children: [
                Expanded(child: _surface),
                OptionsToggle(
                  expanded: _showOptions,
                  onTap: () => _toggleOptions(overlay),
                ),
                OptionsPanel(
                  expanded: _showOptions,
                  controller: _pad,
                  settings: context.read<SettingsController>(),
                ),
                if (showKeyboard)
                  NativeKeyboardInput(
                    bridge: _bridge,
                    sender: context.read<CommandSender>(),
                    haptics: context.read<HapticsService>(),
                  ),
              ],
            ),
            _FloatingKeyboardLayer(
              bridge: _bridge,
              onKeyboardShown: () => setState(() => _showOptions = false),
            ),
          ],
        ),
      ),
    );
  }
}

/// Positions the draggable keyboard button. It is the only part that listens
/// to the button position and the screen size, so dragging it never rebuilds
/// the touchpad.
class _FloatingKeyboardLayer extends StatelessWidget {
  const _FloatingKeyboardLayer({
    required this.bridge,
    required this.onKeyboardShown,
  });

  final HiddenTextBridge bridge;
  final VoidCallback onKeyboardShown;

  @override
  Widget build(BuildContext context) {
    final isReady = context.select<KeyboardOverlayController, bool>(
      (o) => o.isReady,
    );
    final position = context.select<KeyboardOverlayController, Offset>(
      (o) => o.keyboardButtonPosition,
    );
    // sizeOf depends only on the window size, not on the keyboard insets that
    // change on every frame of the keyboard animation.
    final screenSize = MediaQuery.sizeOf(context);
    const buttonSize = FloatingKeyboardButton.defaultSize;
    if (!isReady) return const SizedBox.shrink();

    return Positioned(
      left: FloatingKeyboardButton.clampPosition(
        position.dx,
        buttonSize,
        screenSize.width,
      ),
      top: FloatingKeyboardButton.clampPosition(
        position.dy,
        buttonSize,
        screenSize.height,
      ),
      child: FloatingKeyboardButton(
        bridge: bridge,
        screenSize: screenSize,
        onKeyboardShown: onKeyboardShown,
      ),
    );
  }
}
