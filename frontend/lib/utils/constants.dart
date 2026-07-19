import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:flutter/material.dart';

/// API Configuration
///
/// Django default: `python manage.py runserver` → http://127.0.0.1:8000
///
/// Override only when needed (physical device on Wi‑Fi):
///   flutter run --dart-define=API_BASE_URL=192.168.1.5:8000
class ApiConstants {
  static const String _configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
  );

  /// Django `runserver` default port (do not use 5000 unless you started Django there).
  static const int defaultPort = 8000;

  /// Returns the correct host for the current platform:
  /// - Android emulator → 10.0.2.2 (maps to host machine's localhost)
  /// - Web / Desktop / iOS → 127.0.0.1
  static String get _host {
    if (kIsWeb) return '127.0.0.1';
    if (defaultTargetPlatform == TargetPlatform.android) return '10.0.2.2';
    return '127.0.0.1'; // Windows, macOS, Linux, iOS
  }

  /// On Android emulator, `localhost` / `127.0.0.1` point at the emulator, not your PC.
  static String _androidEmulatorHostFix(String baseUrl) {
    if (defaultTargetPlatform != TargetPlatform.android) return baseUrl;
    final uri = Uri.tryParse(baseUrl);
    if (uri == null) return baseUrl;
    if (uri.host == 'localhost' || uri.host == '127.0.0.1') {
      return uri.replace(host: '10.0.2.2').toString();
    }
    return baseUrl;
  }

  static String get _serverBaseUrl {
    if (_configuredBaseUrl.isNotEmpty) {
      var normalized =
          _configuredBaseUrl.startsWith('http://') ||
              _configuredBaseUrl.startsWith('https://')
          ? _configuredBaseUrl
          : 'http://$_configuredBaseUrl';
      if (normalized.endsWith('/')) {
        normalized = normalized.substring(0, normalized.length - 1);
      }
      return _androidEmulatorHostFix(normalized);
    }
    return 'http://$_host:$defaultPort';
  }

  /// Root API URL (no path). Useful for debugging connection issues.
  static String get serverBaseUrl => _serverBaseUrl;

  static String get baseUrl => '$_serverBaseUrl/api/auth';
  static String get signupEndpoint => '$baseUrl/signup/';
  static String get sendSignupOtpEndpoint => '$baseUrl/signup/send-otp/';
  static String get loginEndpoint => '$baseUrl/login/';
  static String get tokenRefreshEndpoint => '$baseUrl/token/refresh/';

  static String get workersBaseUrl => '$_serverBaseUrl/api/workers';
  static String get workerProfileEndpoint => '$workersBaseUrl/profile/';
  static String get workerAvailabilityEndpoint =>
      '$workersBaseUrl/availability/';
  static String get workerDashboardEndpoint => '$workersBaseUrl/dashboard/';
  static String get workerBookingsEndpoint => '$workersBaseUrl/bookings/';
  static String workerBookingStatusEndpoint(int bookingId) =>
      '$workersBaseUrl/bookings/$bookingId/status/';
  static String get customerBookingCreateEndpoint =>
      '$workersBaseUrl/bookings/create/';
  static String get customerBookingsEndpoint => '$workersBaseUrl/bookings/my/';
  static String bookingReviewEndpoint(int bookingId) =>
      '$workersBaseUrl/bookings/$bookingId/review/';
  static String get conversationsEndpoint => '$workersBaseUrl/conversations/';
  static String conversationMessagesEndpoint(int conversationId) =>
      '$workersBaseUrl/conversations/$conversationId/messages/';
  static String get categoriesEndpoint => '$workersBaseUrl/categories/';
  static String get jobCategoriesEndpoint => '$workersBaseUrl/job-categories/';
  static String get nearbyWorkersEndpoint => '$workersBaseUrl/nearby/';
  static String workerDetailEndpoint(int workerId) =>
      '$workersBaseUrl/$workerId/';
  static String get workerWorkImagesEndpoint =>
      '$workersBaseUrl/profile/work-images/';
  static String workerWorkImageDeleteEndpoint(int imageId) =>
      '$workersBaseUrl/profile/work-images/$imageId/';

  /// Builds a full URL for Django media paths returned by the API.
  static String resolveMediaUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    if (path.startsWith('/')) {
      return '$_serverBaseUrl$path';
    }
    return '$_serverBaseUrl/$path';
  }
}

/// OTP-related constants.
class AuthConstants {
  static const String indiaCountryCode = '+91';
  static const int otpLength = 6;
  static const Duration otpTimeout = Duration(seconds: 60);
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
  static const Color cardBg = Color(0x1AFFFFFF); // 10% white
  static const Color cardBorder = Color(0x33FFFFFF); // 20% white
  static const Color inputFill = Color(0x0DFFFFFF); // 5% white
  static const Color inputBorder = Color(0x26FFFFFF); // 15% white
  static const Color inputFocusBorder = Color(0xFF6C63FF);

  // Text colors
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xB3FFFFFF); // 70% white
  static const Color textHint = Color(0x80FFFFFF); // 50% white

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
