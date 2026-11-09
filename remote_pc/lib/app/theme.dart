import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';

export 'package:remote_pc/app/app_colors.dart';

/// Reproduces the original theme: dark base, black scaffold and app bar,
/// color scheme seeded with blue.
class AppTheme {
  AppTheme._();

  static ThemeData dark() {
    return ThemeData.dark().copyWith(
      scaffoldBackgroundColor: AppColors.black,
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.black,
        elevation: 0,
        centerTitle: true,
      ),
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.blue,
        brightness: Brightness.dark,
      ),
    );
  }
}
