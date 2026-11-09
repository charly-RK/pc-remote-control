import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Persisted user preferences. The keys are the ones used by the original app
/// so existing installs keep their values.
class SettingsSnapshot {
  const SettingsSnapshot({
    this.sensitivity = SettingsRepository.defaultSensitivity,
    this.vibrationEnabled = true,
  });

  final double sensitivity;
  final bool vibrationEnabled;
}

class SettingsRepository {
  static const defaultSensitivity = 2.0;
  static const sensitivityKey = 'sensitivity';
  static const vibrationKey = 'vibration';

  /// Tolerates storage failures by returning the defaults.
  Future<SettingsSnapshot> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return SettingsSnapshot(
        sensitivity: prefs.getDouble(sensitivityKey) ?? defaultSensitivity,
        vibrationEnabled: prefs.getBool(vibrationKey) ?? true,
      );
    } catch (e) {
      debugPrint('Settings load failed: $e');
      return const SettingsSnapshot();
    }
  }

  Future<void> save(SettingsSnapshot snapshot) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setDouble(sensitivityKey, snapshot.sensitivity);
      await prefs.setBool(vibrationKey, snapshot.vibrationEnabled);
    } catch (e) {
      debugPrint('Settings save failed: $e');
    }
  }
}
