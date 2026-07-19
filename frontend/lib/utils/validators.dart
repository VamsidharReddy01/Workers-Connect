/// Form validation functions matching backend constraints.

class Validators {
  /// Validates email format.
  static String? validateEmail(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Email is required';
    }
    final emailRegex = RegExp(r'^[\w\.\-\+]+@[\w\-]+\.[\w\-\.]+$');
    if (!emailRegex.hasMatch(value.trim())) {
      return 'Enter a valid email address';
    }
    return null;
  }

  /// Validates password — minimum 8 characters (matches backend).
  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    return null;
  }

  /// Validates confirm password matches.
  static String? validateConfirmPassword(String? value, String password) {
    if (value == null || value.isEmpty) {
      return 'Please confirm your password';
    }
    if (value != password) {
      return 'Passwords do not match';
    }
    return null;
  }

  /// Validates username — minimum 3 characters.
  static String? validateUsername(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Username is required';
    }
    if (value.trim().length < 3) {
      return 'Username must be at least 3 characters';
    }
    return null;
  }

  /// Validates phone number — optional, but if provided must be valid.
  static String? validatePhoneNumber(String? value) {
    if (value == null || value.trim().isEmpty) {
      return null; // Optional field
    }
    final phoneRegex = RegExp(r'^\+?[\d\s\-]{7,15}$');
    if (!phoneRegex.hasMatch(value.trim())) {
      return 'Enter a valid phone number';
    }
    return null;
  }

  static final RegExp _indianMobileRegex = RegExp(r'^[6-9]\d{9}$');

  /// Validates a 10-digit Indian mobile number (with optional 91 prefix).
  static String? validateIndianPhoneNumber(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Phone number is required';
    }

    final digits = value.replaceAll(RegExp(r'\D'), '');
    if (digits.length == 10 && _indianMobileRegex.hasMatch(digits)) {
      return null;
    }
    if (digits.length == 12 &&
        digits.startsWith('91') &&
        _indianMobileRegex.hasMatch(digits.substring(2))) {
      return null;
    }

    return 'Enter a valid 10-digit Indian mobile number';
  }

  /// Formats a validated Indian number to E.164 (+91XXXXXXXXXX).
  static String formatIndianPhoneE164(String value) {
    final digits = value.replaceAll(RegExp(r'\D'), '');
    if (digits.length == 12 && digits.startsWith('91')) {
      return '+$digits';
    }
    return '+91$digits';
  }

  /// Validates a 6-digit OTP code.
  static String? validateOtp(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'OTP is required';
    }
    if (!RegExp(r'^\d{6}$').hasMatch(value.trim())) {
      return 'Enter a valid 6-digit OTP';
    }
    return null;
  }
}
