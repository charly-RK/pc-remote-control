import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:remote_pc/app/theme.dart';

/// The default test font (Ahem) is far wider than real text and reports
/// overflows that do not exist on a device. Loads Roboto from the Flutter SDK.
/// Returns false (and tests fall back to Ahem) when the SDK fonts are missing.
Future<bool> loadRoboto() async {
  final root = Platform.environment['FLUTTER_ROOT'];
  if (root == null) return false;
  final dir = '$root/bin/cache/artifacts/material_fonts';
  final files = ['roboto-regular.ttf', 'roboto-medium.ttf', 'roboto-bold.ttf'];
  if (!files.every((f) => File('$dir/$f').existsSync())) return false;
  final loader = FontLoader('Roboto');
  for (final f in files) {
    loader.addFont(
      Future.value(ByteData.sublistView(File('$dir/$f').readAsBytesSync())),
    );
  }
  await loader.load();
  return true;
}

ThemeData appThemeWith({required bool realFont}) {
  final base = AppTheme.dark();
  return realFont
      ? base.copyWith(textTheme: base.textTheme.apply(fontFamily: 'Roboto'))
      : base;
}
