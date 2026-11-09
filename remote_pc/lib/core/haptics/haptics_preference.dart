/// Read-only view of the haptics preference. Implemented by the settings
/// controller so `core` does not depend on a feature.
abstract class HapticsPreference {
  bool get vibrationEnabled;
}
