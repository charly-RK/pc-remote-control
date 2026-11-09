import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:remote_pc/app/app_colors.dart';
import 'package:remote_pc/core/network/connection_status.dart' as net;
import 'package:remote_pc/core/network/discovery_service.dart';
import 'package:remote_pc/core/ui/ui_utils.dart';
import 'package:remote_pc/features/connection/domain/manual_input.dart';
import 'package:remote_pc/features/connection/domain/qr_payload.dart';
import 'package:remote_pc/features/connection/presentation/connection_strings.dart';
import 'package:remote_pc/features/connection/presentation/controllers/connection_controller.dart';
import 'package:remote_pc/features/connection/presentation/pages/qr_scanner_page.dart';
import 'package:remote_pc/features/connection/presentation/widgets/connection_dialogs.dart';
import 'package:remote_pc/features/connection/presentation/widgets/connection_fields.dart';
import 'package:remote_pc/features/connection/presentation/widgets/connection_header.dart';

/// First screen: enter the PC address and PIN (or scan the QR) to pair.
class ConnectionScreen extends StatefulWidget {
  const ConnectionScreen({super.key});

  @override
  State<ConnectionScreen> createState() => _ConnectionScreenState();
}

class _ConnectionScreenState extends State<ConnectionScreen> {
  final _ipController = TextEditingController();
  final _pinController = TextEditingController();
  late final ConnectionController _controller;
  bool _manualAttempt = false;
  net.ConnectionStatus _lastStatus = net.ConnectionStatus.idle;

  @override
  void initState() {
    super.initState();
    _controller = context.read<ConnectionController>();
    _controller.addListener(_onControllerChanged);
    _fillSavedHost();
  }

  @override
  void dispose() {
    _controller.removeListener(_onControllerChanged);
    _ipController.dispose();
    _pinController.dispose();
    super.dispose();
  }

  /// Prefills the last used address (the PIN is never stored).
  void _fillSavedHost() {
    final host = _controller.prefillHost;
    if (host != null && _ipController.text.isEmpty) {
      _ipController.text = host;
    }
  }

  /// Reports failures of the automatic reconnection (manual attempts report
  /// their own result).
  void _onControllerChanged() {
    if (!mounted) return;
    _fillSavedHost();
    final status = _controller.status;
    final failedNow =
        status == net.ConnectionStatus.error &&
        _lastStatus != net.ConnectionStatus.error;
    _lastStatus = status;
    final message = _controller.errorMessage;
    if (failedNow && !_manualAttempt && message != null) {
      UiUtils.showSnackBar(context, message, isError: true);
    }
  }

  void _showResult(bool success) {
    if (!mounted) return;
    if (success) {
      UiUtils.showSnackBar(
        context,
        ConnectionStrings.connectOk,
        isSuccess: true,
      );
    } else {
      UiUtils.showSnackBar(
        context,
        _controller.errorMessage ?? ConnectionStrings.connectFailed,
        isError: true,
      );
    }
  }

  Future<void> _connect() async {
    final host = _ipController.text.trim();
    final pin = _pinController.text.trim();
    if (host.isEmpty || pin.isEmpty) {
      UiUtils.showSnackBar(
        context,
        ConnectionStrings.enterIpAndPin,
        isError: true,
      );
      return;
    }
    final input = ManualInput.tryCreate(
      host,
      '${_controller.portFor(host)}',
      pin,
    );
    if (input == null) {
      UiUtils.showSnackBar(
        context,
        ConnectionStrings.invalidData,
        isError: true,
      );
      return;
    }
    _manualAttempt = true;
    final success = await _controller.pairManual(input);
    _manualAttempt = false;
    _showResult(success);
  }

  Future<void> _scanNetwork() async {
    if (!await showSearchDialog(context) || !mounted) return;
    UiUtils.showSnackBar(context, ConnectionStrings.searching);
    await _controller.scanLan();
    if (!mounted) return;
    final found = _controller.discovered;
    if (found.isEmpty) {
      UiUtils.showSnackBar(
        context,
        ConnectionStrings.nothingFound,
        isError: true,
      );
      return;
    }
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    final DiscoveredServer? picked = found.length == 1
        ? found.first
        : await showServerPicker(context, found);
    if (picked == null || !mounted) return;
    setState(() {
      _ipController.text = picked.ip;
      _pinController.text = '';
    });
  }

  Future<void> _scanQrCode() async {
    try {
      final result = await Navigator.push<String>(
        context,
        MaterialPageRoute(builder: (context) => const QRScannerScreen()),
      );
      if (result == null) return;

      final qr = QrPayload.tryParseLenient(result);
      if (qr != null) {
        setState(() {
          _ipController.text = qr.ip;
          _pinController.text = qr.code;
        });
        _manualAttempt = true;
        final success = await _controller.pairWithQr(qr);
        _manualAttempt = false;
        _showResult(success);
        return;
      }

      // Older QR format: only a URL, so no PIN and no automatic connection.
      final uri = Uri.tryParse(result);
      if (uri != null && uri.host.isNotEmpty) {
        setState(() => _ipController.text = uri.host);
        return;
      }
      throw const FormatException('Unknown QR content');
    } on FormatException {
      if (mounted) {
        UiUtils.showSnackBar(
          context,
          ConnectionStrings.qrReadFailed,
          isError: true,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = context.select<ConnectionController, bool>(
      (c) => c.isBusy,
    );
    return Scaffold(
      backgroundColor: AppColors.black,
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [AppColors.backgroundDeep, AppColors.surfaceDark],
              ),
            ),
          ),
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const ConnectionHeader(),
                  const SizedBox(height: 48),
                  IpRow(
                    controller: _ipController,
                    onScanQr: _scanQrCode,
                    onSearch: _scanNetwork,
                  ),
                  const SizedBox(height: 20),
                  PinField(
                    controller: _pinController,
                    onShowInstructions: () => showInstructionsDialog(context),
                  ),
                  const SizedBox(height: 8),
                  const SizedBox(height: 32),
                  ConnectButton(isLoading: isLoading, onPressed: _connect),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
