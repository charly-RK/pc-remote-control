/// Validation of the manual connection form. Returns an error key or null.
enum InputProblem { host, port, pin }

class ManualInput {
  const ManualInput({
    required this.host,
    required this.port,
    required this.pin,
  });

  final String host;
  final int port;
  final String pin;

  static final _hostPattern = RegExp(r'^[A-Za-z0-9.\-]+$');
  static final _pinPattern = RegExp(r'^\d{4,10}$');

  static InputProblem? validate(String host, String port, String pin) {
    final trimmedHost = host.trim();
    if (trimmedHost.isEmpty || !_hostPattern.hasMatch(trimmedHost)) {
      return InputProblem.host;
    }
    final portNumber = int.tryParse(port.trim());
    if (portNumber == null || portNumber < 1 || portNumber > 65535) {
      return InputProblem.port;
    }
    if (!_pinPattern.hasMatch(pin.trim())) return InputProblem.pin;
    return null;
  }

  static ManualInput? tryCreate(String host, String port, String pin) {
    if (validate(host, port, pin) != null) return null;
    return ManualInput(
      host: host.trim(),
      port: int.parse(port.trim()),
      pin: pin.trim(),
    );
  }
}
