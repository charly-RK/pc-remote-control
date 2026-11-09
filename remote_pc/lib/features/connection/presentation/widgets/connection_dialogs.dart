import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/network/discovery_service.dart';
import 'package:remote_pc/features/connection/presentation/connection_strings.dart';

/// Asks before searching the network. Resolves true when the user accepts.
Future<bool> showSearchDialog(BuildContext context) async {
  final accepted = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text(ConnectionStrings.searchDialogTitle),
      content: const SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search, size: 50, color: AppColors.blue),
            SizedBox(height: 16),
            Text(ConnectionStrings.searchQuestion, textAlign: TextAlign.center),
            SizedBox(height: 16),
            Text(
              ConnectionStrings.searchHelp,
              style: TextStyle(fontSize: 12, color: AppColors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text(ConnectionStrings.cancel),
        ),
        ElevatedButton(
          onPressed: () => Navigator.pop(context, true),
          child: const Text(ConnectionStrings.search),
        ),
      ],
    ),
  );
  return accepted ?? false;
}

/// Lets the user pick one of several discovered servers.
Future<DiscoveredServer?> showServerPicker(
  BuildContext context,
  List<DiscoveredServer> servers,
) {
  return showDialog<DiscoveredServer>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text(ConnectionStrings.pickServerTitle),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final server in servers)
              ListTile(
                leading: const Icon(Icons.computer, color: AppColors.blue),
                title: Text(server.name),
                subtitle: Text('${server.ip}:${server.port}'),
                onTap: () => Navigator.pop(context, server),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text(ConnectionStrings.cancel),
        ),
      ],
    ),
  );
}

class _InstructionStep extends StatelessWidget {
  const _InstructionStep({required this.number, required this.text});

  final int number;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: AppColors.blue,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                '$number',
                style: const TextStyle(
                  color: AppColors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

Future<void> showInstructionsDialog(BuildContext context) {
  return showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text(ConnectionStrings.instructionsTitle),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              ConnectionStrings.instructionsIntro,
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            for (var i = 0; i < ConnectionStrings.instructionSteps.length; i++)
              _InstructionStep(
                number: i + 1,
                text: ConnectionStrings.instructionSteps[i],
              ),
            const SizedBox(height: 10),
            const Divider(),
            const SizedBox(height: 10),
            const Text(
              ConnectionStrings.portNote,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: AppColors.blue,
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text(ConnectionStrings.understood),
        ),
      ],
    ),
  );
}
