import 'package:flutter/material.dart';
import '../models/user_model.dart';
import 'auth_service.dart';
import 'profile_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();
  final ProfileService _profileService = ProfileService();

  UserModel? _user;
  bool _isLoading = false;
  String? _errorMessage;

  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _user != null;

  /// Restores session from secure storage (usually called on splash screen).
  Future<bool> checkSession() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final loggedIn = await _authService.isLoggedIn();
      if (loggedIn) {
        final storedUser = await _authService.getStoredUser();
        if (storedUser != null) {
          final freshUser = await _profileService.getProfile();
          if (freshUser != null) {
            await _authService.saveUser(freshUser);
            _user = freshUser;
          } else if (_profileService.lastErrorMessage?.toLowerCase().contains(
                'session expired',
              ) ??
              false) {
            await _authService.logout();
            _user = null;
            _isLoading = false;
            notifyListeners();
            return false;
          } else {
            _user = storedUser;
          }
          _isLoading = false;
          notifyListeners();
          return true;
        }
      }
    } catch (e) {
      _errorMessage = 'Session restore failed.';
    }

    _user = null;
    _isLoading = false;
    notifyListeners();
    return false;
  }

  /// Logs in the user, updating provider states accordingly.
  Future<bool> login({required String email, required String password}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final result = await _authService.login(email: email, password: password);

    _isLoading = false;
    if (result.success && result.user != null) {
      _user = result.user;
      notifyListeners();
      return true;
    } else {
      _errorMessage = result.error ?? 'Authentication failed.';
      _user = null;
      notifyListeners();
      return false;
    }
  }

  /// Registers a new user, updating provider states accordingly.
  Future<bool> signup({
    required String username,
    required String email,
    required String password,
    required String role,
    required String emailOtp,
    String? phoneNumber,
    String? location,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final result = await _authService.signup(
      username: username,
      email: email,
      password: password,
      role: role,
      emailOtp: emailOtp,
      phoneNumber: phoneNumber,
      location: location,
    );

    _isLoading = false;
    if (result.success && result.user != null) {
      _user = result.user;
      notifyListeners();
      return true;
    } else {
      _errorMessage = result.error ?? 'Registration failed.';
      _user = null;
      notifyListeners();
      return false;
    }
  }

  Future<bool> sendSignupOtp({required String email}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final result = await _authService.sendSignupOtp(email: email);

    _isLoading = false;
    if (result.success) {
      notifyListeners();
      return true;
    }

    _errorMessage = result.error ?? 'Could not send OTP. Please try again.';
    notifyListeners();
    return false;
  }

  /// Manual / Automatic JWT access token refresh handler.
  Future<bool> refreshSessionToken() async {
    final success = await _authService.refreshToken();
    if (success) {
      // Re-read user metadata to ensure fully synced
      final storedUser = await _authService.getStoredUser();
      if (storedUser != null) {
        _user = storedUser;
        notifyListeners();
      }
      return true;
    } else {
      _user = null;
      notifyListeners();
      return false;
    }
  }

  /// Logs out the user completely, clearing all cached data.
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    await _authService.logout();

    _user = null;
    _isLoading = false;
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> updateUser(UserModel user) async {
    _user = user;
    await _authService.saveUser(user);
    notifyListeners();
  }

  Future<bool> refreshUserProfile() async {
    final freshUser = await _profileService.getProfile();
    if (freshUser == null) {
      if (_profileService.lastErrorMessage?.toLowerCase().contains(
            'session expired',
          ) ??
          false) {
        await logout();
      }
      return false;
    }

    await updateUser(freshUser);
    return true;
  }
}
