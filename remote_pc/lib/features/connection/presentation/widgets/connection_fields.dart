import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/features/connection/presentation/connection_strings.dart';

OutlineInputBorder _border(Color color) => OutlineInputBorder(
  borderRadius: BorderRadius.circular(12),
  borderSide: BorderSide(color: color),
);

/// Square button next to the IP field (QR scan, network search).
class SquareIconButton extends StatelessWidget {
  const SquareIconButton({
    super.key,
    required this.icon,
    required this.tooltip,
    required this.onPressed,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        color: AppColors.blue.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.blue.withValues(alpha: 0.3)),
      ),
      child: IconButton(
        icon: Icon(icon, color: AppColors.blue),
        onPressed: onPressed,
        tooltip: tooltip,
      ),
    );
  }
}

/// IP field with the QR and search buttons.
class IpRow extends StatelessWidget {
  const IpRow({
    super.key,
    required this.controller,
    required this.onScanQr,
    required this.onSearch,
  });

  final TextEditingController controller;
  final VoidCallback onScanQr;
  final VoidCallback onSearch;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            style: const TextStyle(color: AppColors.white),
            decoration: InputDecoration(
              labelText: ConnectionStrings.ipLabel,
              hintText: ConnectionStrings.ipHint,
              labelStyle: const TextStyle(color: AppColors.grey),
              prefixIcon: const Icon(Icons.computer, color: AppColors.blue),
              enabledBorder: _border(AppColors.grey),
              focusedBorder: _border(AppColors.blue),
              filled: true,
              fillColor: AppColors.grey900,
            ),
            keyboardType: TextInputType.number,
          ),
        ),
        const SizedBox(width: 8),
        SquareIconButton(
          icon: Icons.qr_code_scanner,
          tooltip: ConnectionStrings.scanQrTooltip,
          onPressed: onScanQr,
        ),
        const SizedBox(width: 8),
        SquareIconButton(
          icon: Icons.search,
          tooltip: ConnectionStrings.searchTooltip,
          onPressed: onSearch,
        ),
      ],
    );
  }
}

/// PIN field with the instructions button.
class PinField extends StatelessWidget {
  const PinField({
    super.key,
    required this.controller,
    required this.onShowInstructions,
  });

  final TextEditingController controller;
  final VoidCallback onShowInstructions;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      style: const TextStyle(color: AppColors.white),
      decoration: InputDecoration(
        labelText: ConnectionStrings.pinLabel,
        hintText: ConnectionStrings.pinHint,
        labelStyle: const TextStyle(color: AppColors.grey),
        prefixIcon: const Icon(Icons.vpn_key, color: AppColors.blue),
        suffixIcon: IconButton(
          icon: const Icon(Icons.info, size: 20),
          onPressed: onShowInstructions,
          color: AppColors.blue.withValues(alpha: 0.7),
        ),
        enabledBorder: _border(AppColors.grey),
        focusedBorder: _border(AppColors.blue),
        filled: true,
        fillColor: AppColors.grey900,
      ),
      keyboardType: TextInputType.number,
      obscureText: true,
      maxLength: 6,
    );
  }
}

/// Primary connect button with its loading state.
class ConnectButton extends StatelessWidget {
  const ConnectButton({
    super.key,
    required this.isLoading,
    required this.onPressed,
  });

  final bool isLoading;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 56,
      child: ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.blue,
          foregroundColor: AppColors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 4,
          shadowColor: AppColors.blue.withValues(alpha: 0.5),
        ),
        child: isLoading
            ? const SizedBox(
                height: 24,
                width: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.white,
                ),
              )
            : const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.link, size: 24),
                  SizedBox(width: 12),
                  Text(
                    ConnectionStrings.connectButton,
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
      ),
    );
  }
}
