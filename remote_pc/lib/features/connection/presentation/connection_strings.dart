import 'package:remote_pc/core/network/remote_connection.dart';
import 'package:remote_pc/core/protocol/protocol.dart';

/// Spanish texts of the connection feature (wording of the original app).
class ConnectionStrings {
  ConnectionStrings._();

  // Connection screen.
  static const title = 'Control Remoto PC';
  static const subtitle = 'Controla tu PC desde tu dispositivo móvil';
  static const ipLabel = 'Dirección IP del PC';
  static const ipHint = 'Ej: 192.168.1.100';
  static const pinLabel = 'Código PIN';
  static const pinHint = '6 dígitos (mostrado en el PC)';
  static const connectButton = 'CONECTAR AL PC';
  static const scanQrTooltip = 'Escanear código QR';
  static const searchTooltip = 'Buscar PC en la red';
  static const enterIpAndPin = 'Ingrese IP y PIN para continuar';
  static const invalidData = 'La IP o el PIN no son válidos';
  static const connectFailed = 'No se pudo establecer conexión';
  static const connectOk = 'Conexión establecida correctamente';
  static const qrReadFailed = 'No se pudo leer el código QR';

  // Search dialog.
  static const searchDialogTitle = 'Buscar PC';
  static const searchQuestion = '¿Deseas buscar servidores en tu red?';
  static const searchHelp =
      'Esta función buscará automáticamente servidores de control en la red local.';
  static const cancel = 'Cancelar';
  static const search = 'Buscar';
  static const searching = 'Buscando PCs en tu red...';
  static const nothingFound = 'No se encontraron PCs en tu red';
  static const pickServerTitle = 'Selecciona un PC';

  // Instructions dialog.
  static const instructionsTitle = 'Instrucciones';
  static const instructionsIntro = 'Para conectar:';
  static const instructionSteps = <String>[
    'Ejecuta el servidor en tu PC',
    'Anota la IP y PIN que se muestran',
    'Ingresa los datos en esta app',
    'Presiona CONECTAR',
  ];
  static const portNote = 'Puerto: $defaultServerPort';
  static const understood = 'Entendido';

  // QR scanner.
  static const scannerLine1 = 'Alinee el código QR dentro del';
  static const scannerLine2 = 'marco para escanear';

  // Status widget.
  static const statusDisconnected = 'Desconectado';
  static const statusConnecting = 'Conectando...';
  static const statusConnected = 'Conectado ✓';
  static const statusPending = 'Conectado (pendiente autenticación)';
  static const disconnect = 'Desconectar';
  static String connectedToHost(String host) => 'Conectado a: $host';
  static String errorPrefix(String message) => 'Error: $message';

  // Background notification.
  static String connectedTo(String name) => 'Conectado a $name';

  /// Maps a failure code to a user-facing message.
  static String forFailure(ConnectionFailure failure) {
    switch (failure.code) {
      case ErrorCodes.invalidPin:
        return 'PIN incorrecto';
      case ErrorCodes.invalidToken:
        return 'Este dispositivo ya no está vinculado. Vuelve a vincularlo';
      case ErrorCodes.rateLimited:
        return 'Demasiados intentos. Espera un minuto';
      case ConnectionFailure.timeout:
        return 'Tiempo de espera agotado';
      case ConnectionFailure.network:
        return 'No se pudo conectar al PC';
      default:
        return 'No se pudo conectar';
    }
  }
}
