import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Connection saved by the first version of the app (IP and PIN in plain
/// shared preferences).
class LegacyConnection {
  const LegacyConnection({required this.ip, required this.pin});

  final String ip;
  final String pin;
}

/// Reads and removes the legacy data once. The PIN is never kept afterwards:
/// the token obtained by pairing replaces it.
abstract class LegacyConnectionSource {
  Future<LegacyConnection?> take();
}

class PrefsLegacyConnectionSource implements LegacyConnectionSource {
  static const ipKey = 'last_ip';
  static const pinKey = 'last_pin';

  @override
  Future<LegacyConnection?> take() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final ip = prefs.getString(ipKey);
      final pin = prefs.getString(pinKey);
      if (ip == null && pin == null) return null;
      await prefs.remove(pinKey);
      await prefs.remove(ipKey);
      if (ip == null || ip.isEmpty || pin == null || pin.isEmpty) return null;
      return LegacyConnection(ip: ip, pin: pin);
    } on Object catch (error) {
      debugPrint('Legacy connection could not be read: $error');
      return null;
    }
  }
}
