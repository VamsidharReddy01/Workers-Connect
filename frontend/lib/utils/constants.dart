import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:flutter/material.dart';

/// API Configuration
class ApiConstants {
  /// Returns the correct host for the current platform:
  /// - Android emulator → 10.0.2.2 (maps to host's localhost)
  /// - Web / Desktop / iOS → localhost
  static String get _host {
    if (kIsWeb) return 'localhost';
    if (defaultTargetPlatform == TargetPlatform.android) return '10.0.2.2';
    return 'localhost'; // Windows, macOS, Linux, iOS
  }

  static String get baseUrl => 'http://$_host:8000/api/auth';
  static String get signupEndpoint => '$baseUrl/signup/';
  static String get loginEndpoint => '$baseUrl/login/';
  static String get tokenRefreshEndpoint => '$baseUrl/token/refresh/';
}

/// Secure Storage Keys
class StorageKeys {
  static const String accessToken = 'access_token';
  static const String refreshToken = 'refresh_token';
  static const String userId = 'user_id';
  static const String username = 'username';
  static const String email = 'user_email';
  static const String role = 'user_role';
  static const String location = 'user_location';
}

/// App Color Palette
class AppColors {
  // Light Mode Color Palette (for Onboarding UI matching Screenshots)
  static const Color lightBg = Color(0xFFF8FAFC);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightPrimary = Color(0xFF3444F4);
  static const Color lightAccent = Color(0xFF5E6DF8);
  static const Color lightBorder = Color(0xFFE2E6F2);
  static const Color lightTextPrimary = Color(0xFF1E212D);
  static const Color lightTextSecondary = Color(0xFF6E7489);
  static const Color lightTextHint = Color(0xFFA2A7B8);
  static const Color lightInputFill = Color(0xFFFDFDFD);

  // Primary gradient colors
  static const Color primaryDark = Color(0xFF0A0E21);
  static const Color primaryMid = Color(0xFF1A1F3A);
  static const Color accentViolet = Color(0xFF6C63FF);
  static const Color accentBlue = Color(0xFF00D4FF);
  static const Color accentPink = Color(0xFFFF6B9D);

  // Surface colors
  static const Color cardBg = Color(0x1AFFFFFF);       // 10% white
  static const Color cardBorder = Color(0x33FFFFFF);    // 20% white
  static const Color inputFill = Color(0x0DFFFFFF);     // 5% white
  static const Color inputBorder = Color(0x26FFFFFF);   // 15% white
  static const Color inputFocusBorder = Color(0xFF6C63FF);

  // Text colors
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xB3FFFFFF); // 70% white
  static const Color textHint = Color(0x80FFFFFF);      // 50% white

  // Status colors
  static const Color error = Color(0xFFFF5252);
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFFA726);

  // Gradient presets
  static const LinearGradient backgroundGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primaryDark, Color(0xFF141A3A), Color(0xFF0D1230)],
  );

  static const LinearGradient buttonGradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [accentViolet, Color(0xFF8B7FFF), accentBlue],
  );

  static const LinearGradient cardGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0x1AFFFFFF), Color(0x0DFFFFFF)],
  );
}
