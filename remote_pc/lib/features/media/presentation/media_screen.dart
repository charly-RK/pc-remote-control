import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/network/command_sender.dart';
import 'package:remote_pc/core/protocol/protocol.dart';
import 'package:remote_pc/features/media/presentation/controllers/media_controller.dart';
import 'package:remote_pc/features/media/presentation/media_strings.dart';

class MediaScreen extends StatefulWidget {
  const MediaScreen({super.key});

  @override
  State<MediaScreen> createState() => _MediaScreenState();
}

class _MediaScreenState extends State<MediaScreen> {
  late final MediaController _media;
  Timer? _poll;

  @override
  void initState() {
    super.initState();
    _media = MediaController(context.read<CommandSender>());
    // The screen is destroyed when the tab is left, so it polls only while visible.
    _media.refresh();
    _poll = Timer.periodic(const Duration(seconds: 2), (_) => _media.refresh());
  }

  @override
  void dispose() {
    _poll?.cancel();
    _media.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Scrolls only when the content does not fit (small phones); otherwise it
    // keeps the centered layout.
    return LayoutBuilder(
      builder: (context, box) => SingleChildScrollView(
        child: ConstrainedBox(
          constraints: BoxConstraints(minHeight: box.maxHeight),
          child: ListenableBuilder(
            listenable: _media,
            builder: (context, _) => _buildContent(),
          ),
        ),
      ),
    );
  }

  Widget _buildContent() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Text(
          MediaStrings.title,
          style: TextStyle(
            fontSize: 24,
            color: AppColors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 30),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _MediaButton(
              icon: Icons.skip_previous,
              color: AppColors.orange,
              label: MediaStrings.previous,
              onPressed: () => _media.send(MediaCommand.previous),
              size: 60,
            ),
            const SizedBox(width: 20),
            _MediaButton(
              icon: _media.playing ? Icons.pause : Icons.play_arrow,
              color: AppColors.green,
              label: MediaStrings.playPause,
              onPressed: () => _media.send(MediaCommand.playPause),
              size: 80,
            ),
            const SizedBox(width: 20),
            _MediaButton(
              icon: Icons.skip_next,
              color: AppColors.orange,
              label: MediaStrings.next,
              onPressed: () => _media.send(MediaCommand.next),
              size: 60,
            ),
          ],
        ),
        const SizedBox(height: 40),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _MediaButton(
              icon: Icons.volume_down,
              color: AppColors.blue,
              label: MediaStrings.volumeDown,
              onPressed: () => _media.send(MediaCommand.volumeDown),
            ),
            const SizedBox(width: 20),
            _MediaButton(
              icon: Icons.volume_mute,
              color: AppColors.red,
              label: MediaStrings.mute,
              onPressed: () => _media.send(MediaCommand.mute),
            ),
            const SizedBox(width: 20),
            _MediaButton(
              icon: Icons.volume_up,
              color: AppColors.blue,
              label: MediaStrings.volumeUp,
              onPressed: () => _media.send(MediaCommand.volumeUp),
            ),
          ],
        ),
        const SizedBox(height: 20),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40),
          child: Row(
            children: [
              const Icon(Icons.volume_mute, color: AppColors.grey, size: 20),
              Expanded(
                child: Slider(
                  value: _media.volume,
                  min: 0.0,
                  max: 1.0,
                  activeColor: AppColors.blue,
                  inactiveColor: AppColors.grey800,
                  onChanged: _media.volumeChanged,
                  onChangeEnd: _media.volumeChangeEnd,
                ),
              ),
              const Icon(Icons.volume_up, color: AppColors.grey, size: 20),
            ],
          ),
        ),
        const SizedBox(height: 20),
        const Text(
          MediaStrings.additionalControls,
          style: TextStyle(color: AppColors.grey, fontSize: 16),
        ),
        const SizedBox(height: 20),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: SizedBox(
            height: 200,
            child: GridView.count(
              crossAxisCount: 3,
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _SmallMediaButton(
                  label: MediaStrings.gameBar,
                  icon: Icons.games,
                  color: AppColors.green,
                  onPressed: () => _media.send(MediaCommand.gameBar),
                ),
                _SmallMediaButton(
                  label: MediaStrings.record,
                  icon: Icons.fiber_manual_record,
                  color: AppColors.red,
                  onPressed: () => _media.send(MediaCommand.record),
                ),
                _SmallMediaButton(
                  label: MediaStrings.micMute,
                  icon: Icons.mic_off,
                  color: AppColors.purple,
                  onPressed: () => _media.send(MediaCommand.micMute),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _MediaButton extends StatelessWidget {
  const _MediaButton({
    required this.icon,
    required this.color,
    required this.label,
    required this.onPressed,
    this.size = 50,
  });

  final IconData icon;
  final Color color;
  final String label;
  final VoidCallback onPressed;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(size / 2),
            border: Border.all(color: color.withValues(alpha: 0.3)),
          ),
          child: IconButton(
            icon: Icon(icon, size: size * 0.5, color: color),
            onPressed: onPressed,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: TextStyle(color: AppColors.grey, fontSize: size * 0.12),
        ),
      ],
    );
  }
}

class _SmallMediaButton extends StatelessWidget {
  const _SmallMediaButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.onPressed,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: color.withValues(alpha: 0.1),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 1,
              style: const TextStyle(color: AppColors.grey, fontSize: 10),
            ),
          ),
        ],
      ),
    );
  }
}
