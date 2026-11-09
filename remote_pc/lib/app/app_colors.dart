import 'package:flutter/material.dart';

/// Single source of colors. Values are identical to the ones used by the
/// original hand-built screens; widgets must not hardcode colors.
class AppColors {
  AppColors._();

  // Base palette (same objects as the original Colors.* usage).
  static const Color blue = Colors.blue;
  static const Color white = Colors.white;
  static const Color black = Colors.black;
  static const Color red = Colors.red;
  static const Color orange = Colors.orange;
  static const Color green = Colors.green;
  static const Color purple = Colors.purple;
  static const Color cyan = Colors.cyan;
  static const Color amber = Colors.amber;
  static const Color transparent = Colors.transparent;

  // Greys (original used Colors.grey, Colors.grey[200..900]).
  static const MaterialColor grey = Colors.grey;
  static final Color grey200 = Colors.grey[200]!;
  static final Color grey300 = Colors.grey[300]!;
  static final Color grey400 = Colors.grey[400]!;
  static final Color grey500 = Colors.grey[500]!;
  static final Color grey600 = Colors.grey[600]!;
  static final Color grey700 = Colors.grey[700]!;
  static final Color grey800 = Colors.grey[800]!;
  static final Color grey850 = Colors.grey[850]!;
  static final Color grey900 = Colors.grey[900]!;

  // Literal colors used by the original screens.
  static const Color dangerDark = Color(0xFFD32F2F);
  static const Color successDark = Color(0xFF2E7D32);
  static const Color snackBar = Color(0xFF323232);
  static const Color surfaceDark = Color(0xFF1A1A1A);
  static const Color backgroundDeep = Color(0xFF0A0A0A);

  // Semantic aliases.
  static const Color background = Colors.black;
  static const Color accent = Colors.blue;
  static const Color error = Colors.red;
  static const Color warning = Colors.orange;
  static const Color success = Colors.green;
  static const Color onDark = Colors.white;

  // Legacy tokens of the generated features. They are kept only until the
  // control features are migrated; do not use them in new code.
  static const Color primary = Color(0xFF4361EE);
  static const Color secondary = Color(0xFF3A0CA3);
  static const Color danger = Color(0xFFF72585);
  static const Color surface = Color(0xFF1A1D29);
  static const Color border = Color(0xFF2D3748);
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFF94A3B8);
}
