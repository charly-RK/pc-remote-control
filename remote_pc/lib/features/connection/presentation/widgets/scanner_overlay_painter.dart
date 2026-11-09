import 'package:flutter/material.dart';
import 'package:remote_pc/app/app_colors.dart';

/// Corner marks of the QR scanning frame.
class ScannerOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppColors.white
      ..strokeWidth = 4
      ..style = PaintingStyle.stroke;

    const corner = 20.0;
    final w = size.width;
    final h = size.height;

    // Top left.
    canvas.drawLine(Offset.zero, const Offset(0, corner), paint);
    canvas.drawLine(Offset.zero, const Offset(corner, 0), paint);
    // Top right.
    canvas.drawLine(Offset(w, 0), Offset(w, corner), paint);
    canvas.drawLine(Offset(w, 0), Offset(w - corner, 0), paint);
    // Bottom left.
    canvas.drawLine(Offset(0, h), Offset(0, h - corner), paint);
    canvas.drawLine(Offset(0, h), Offset(corner, h), paint);
    // Bottom right.
    canvas.drawLine(Offset(w, h), Offset(w, h - corner), paint);
    canvas.drawLine(Offset(w, h), Offset(w - corner, h), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
