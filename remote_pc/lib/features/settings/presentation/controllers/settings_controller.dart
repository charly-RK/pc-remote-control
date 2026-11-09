import 'package:flutter/foundation.dart';
import 'package:remote_pc/core/haptics/haptics_preference.dart';
import 'package:remote_pc/features/settings/data/settings_repository.dart';

class SettingsController extends ChangeNotifier implements HapticsPreference {
  SettingsController(this._repo);

  static const double minSensitivity = 0.5;
  static const double maxSensitivity = 5.0;

  final SettingsRepository _repo;
  SettingsSnapshot _snapshot = const SettingsSnapshot();
  Future<void> _saveChain = Future<void>.value();

  /// Completes when all queued writes have finished (writes are serialized so
  /// the last change always wins).
  Future<void> get pendingSave => _saveChain;

  double get sensitivity => _snapshot.sensitivity;

  @override
  bool get vibrationEnabled => _snapshot.vibrationEnabled;

  Future<void> load() async {
    _snapshot = await _repo.load();
    notifyListeners();
  }

  set sensitivity(double value) => _update(
    SettingsSnapshot(
      sensitivity: value.clamp(minSensitivity, maxSensitivity).toDouble(),
      vibrationEnabled: _snapshot.vibrationEnabled,
    ),
  );

  set vibrationEnabled(bool value) => _update(
    SettingsSnapshot(
      sensitivity: _snapshot.sensitivity,
      vibrationEnabled: value,
    ),
  );

  void _update(SettingsSnapshot next) {
    _snapshot = next;
    notifyListeners();
    _saveChain = _saveChain.then((_) => _repo.save(next));
  }
}
