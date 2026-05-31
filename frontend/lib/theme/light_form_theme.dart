import 'package:flutter/material.dart';

/// Light theme for onboarding / job-profile forms (overrides app-wide dark theme).
class LightFormTheme {
  LightFormTheme._();

  static ThemeData of(BuildContext context) {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: const Color(0xFFF8FAFC),
      canvasColor: Colors.white,
      splashColor: const Color(0xFF3444F4).withValues(alpha: 0.08),
      highlightColor: const Color(0xFF3444F4).withValues(alpha: 0.05),
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF3444F4),
        brightness: Brightness.light,
        surface: Colors.white,
        onSurface: const Color(0xFF1E212D),
      ),
      dropdownMenuTheme: const DropdownMenuThemeData(
        textStyle: TextStyle(
          color: Color(0xFF1E212D),
          fontSize: 15,
          fontWeight: FontWeight.w500,
        ),
        menuStyle: MenuStyle(
          backgroundColor: WidgetStatePropertyAll(Colors.white),
          surfaceTintColor: WidgetStatePropertyAll(Colors.white),
          elevation: WidgetStatePropertyAll(8),
          shadowColor: WidgetStatePropertyAll(Color(0x1A000000)),
        ),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
      ),
    );
  }
}
