import 'package:flutter/services.dart';
import 'package:remote_pc/core/haptics/haptics_preference.dart';

/// Haptic feedback that respects the user's vibration setting.
class HapticsService {
  HapticsService(this._preference);

  final HapticsPreference _preference;

  void light() => _run(HapticFeedback.lightImpact);

  void medium() => _run(HapticFeedback.mediumImpact);

  void heavy() => _run(HapticFeedback.heavyImpact);

  void selection() => _run(HapticFeedback.selectionClick);

  void _run(Future<void> Function() feedback) {
    if (!_preference.vibrationEnabled) return;
    feedback();
  }
}
