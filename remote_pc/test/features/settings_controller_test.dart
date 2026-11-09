import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/core/haptics/haptics_service.dart';
import 'package:remote_pc/features/settings/data/settings_repository.dart';
import 'package:remote_pc/features/settings/presentation/controllers/settings_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../helpers/recording_connection.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('defaults match the original app', () async {
    final settings = SettingsController(SettingsRepository());
    await settings.load();
    expect(settings.sensitivity, 2.0);
    expect(settings.vibrationEnabled, isTrue);
  });

  test('reads the values saved by the original app', () async {
    SharedPreferences.setMockInitialValues({
      'sensitivity': 3.5,
      'vibration': false,
    });
    final settings = SettingsController(SettingsRepository());
    await settings.load();
    expect(settings.sensitivity, 3.5);
    expect(settings.vibrationEnabled, isFalse);
  });

  test('persists with the original keys', () async {
    final settings = SettingsController(SettingsRepository());
    await settings.load();
    settings.sensitivity = 4.0;
    settings.vibrationEnabled = false;
    await settings.pendingSave;

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getDouble('sensitivity'), 4.0);
    expect(prefs.getBool('vibration'), isFalse);
  });

  test('sensitivity is clamped to the slider range', () async {
    final settings = SettingsController(SettingsRepository());
    settings.sensitivity = 99;
    expect(settings.sensitivity, SettingsController.maxSensitivity);
    settings.sensitivity = 0;
    expect(settings.sensitivity, SettingsController.minSensitivity);
  });

  test('notifies listeners on change', () async {
    final settings = SettingsController(SettingsRepository());
    var notifications = 0;
    settings.addListener(() => notifications++);
    settings.vibrationEnabled = false;
    settings.sensitivity = 1.0;
    expect(notifications, 2);
  });

  test('haptics respect the vibration setting', () async {
    final messenger = TestWidgetsFlutterBinding.instance.defaultBinaryMessenger;
    final calls = mockHaptics(messenger);
    final settings = SettingsController(SettingsRepository());
    final haptics = HapticsService(settings);

    haptics.light();
    await Future<void>.delayed(Duration.zero);
    expect(calls, ['HapticFeedbackType.lightImpact']);

    settings.vibrationEnabled = false;
    haptics.medium();
    haptics.heavy();
    haptics.selection();
    await Future<void>.delayed(Duration.zero);
    expect(calls.length, 1);
  });
}
