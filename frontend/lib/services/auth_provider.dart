import 'package:flutter/material.dart';
import '../models/user_model.dart';
import 'auth_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();

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
          _user = storedUser;
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
}
