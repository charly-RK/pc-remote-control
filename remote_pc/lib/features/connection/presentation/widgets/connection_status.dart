import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/network/connection_status.dart' as net;
import 'package:remote_pc/features/connection/presentation/connection_strings.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';

/// Status card shown over the control screens. Same widget name as the
/// original app; the network enum is imported with a prefix to avoid the
/// name clash.
class ConnectionStatus extends StatelessWidget {
  const ConnectionStatus({super.key, required this.onDisconnect});

  final VoidCallback onDisconnect;

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<ConnectionController>();

    var statusText = ConnectionStrings.statusDisconnected;
    var statusColor = AppColors.red;

    switch (controller.status) {
      case net.ConnectionStatus.ready:
        statusText = ConnectionStrings.statusConnected;
        statusColor = AppColors.green;
      case net.ConnectionStatus.authenticating:
        statusText = ConnectionStrings.statusPending;
        statusColor = AppColors.blue;
      case net.ConnectionStatus.connecting:
      case net.ConnectionStatus.searching:
      case net.ConnectionStatus.reconnecting:
        statusText = ConnectionStrings.statusConnecting;
        statusColor = AppColors.orange;
      case net.ConnectionStatus.idle:
      case net.ConnectionStatus.error:
        break;
    }

    final connected = controller.status == net.ConnectionStatus.ready;
    final showClose =
        connected || controller.status == net.ConnectionStatus.authenticating;
    final host = controller.current?.ip;
    final error = controller.errorMessage;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.black.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: statusColor.withValues(alpha: 0.3), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      color: statusColor,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    statusText,
                    style: const TextStyle(
                      color: AppColors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              if (showClose)
                IconButton(
                  icon: const Icon(Icons.close, color: AppColors.white),
                  onPressed: onDisconnect,
                  tooltip: ConnectionStrings.disconnect,
                ),
            ],
          ),
          if (connected && host != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                ConnectionStrings.connectedToHost(host),
                style: const TextStyle(color: AppColors.grey, fontSize: 12),
              ),
            ),
          if (error != null && error.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                ConnectionStrings.errorPrefix(error),
                style: const TextStyle(color: AppColors.red, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }
}
