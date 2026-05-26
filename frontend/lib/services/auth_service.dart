import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user_model.dart';
import '../utils/constants.dart';
import 'api_service.dart';

/// High-level authentication service.
///
/// Handles signup, login, token management, and session persistence
/// using [flutter_secure_storage] for secure JWT storage.
class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  final ApiService _api = ApiService();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  // ─── SIGNUP ─────────────────────────────────────────────

  /// Registers a new user and returns the user on success.
  /// Tokens are stored automatically.
  Future<({bool success, UserModel? user, String? error})> signup({
    required String username,
    required String email,
    required String password,
    required String role,
    String? phoneNumber,
    String? location,
  }) async {
    final body = <String, dynamic>{
      'username': username.trim(),
      'email': email.trim().toLowerCase(),
      'password': password,
      'role': role,
    };
    if (phoneNumber != null && phoneNumber.trim().isNotEmpty) {
      body['phone_number'] = phoneNumber.trim();
    }
    if (location != null && location.trim().isNotEmpty) {
      body['location'] = location.trim();
    }

    final result = await _api.post(
      ApiConstants.signupEndpoint,
      body: body,
    );

    if (result.success && result.data != null) {
      final user = UserModel.fromJson(result.data!['user']);
      await _storeSession(
        accessToken: result.data!['access'],
        refreshToken: result.data!['refresh'],
        user: user,
      );
      return (success: true, user: user, error: null);
    }

    return (success: false, user: null, error: result.errorMessage);
  }

  // ─── LOGIN ──────────────────────────────────────────────

  /// Authenticates a user and returns the user on success.
  /// Tokens are stored automatically.
  Future<({bool success, UserModel? user, String? error})> login({
    required String email,
    required String password,
  }) async {
    final result = await _api.post(
      ApiConstants.loginEndpoint,
      body: {
        'email': email.trim().toLowerCase(),
        'password': password,
      },
    );

    if (result.success && result.data != null) {
      final user = UserModel.fromJson(result.data!['user']);
      await _storeSession(
        accessToken: result.data!['access'],
        refreshToken: result.data!['refresh'],
        user: user,
      );
      return (success: true, user: user, error: null);
    }

    return (success: false, user: null, error: result.errorMessage);
  }

  // ─── TOKEN REFRESH ──────────────────────────────────────

  /// Refreshes the access token using the stored refresh token.
  Future<bool> refreshToken() async {
    final refresh = await _storage.read(key: StorageKeys.refreshToken);
    if (refresh == null) return false;

    final result = await _api.post(
      ApiConstants.tokenRefreshEndpoint,
      body: {'refresh': refresh},
    );

    if (result.success && result.data != null) {
      await _storage.write(
        key: StorageKeys.accessToken,
        value: result.data!['access'],
      );
      return true;
    }

    // Refresh token expired — force logout
    await logout();
    return false;
  }

  // ─── SESSION MANAGEMENT ─────────────────────────────────

  /// Returns the stored access token, or null if not logged in.
  Future<String?> getAccessToken() async {
    return await _storage.read(key: StorageKeys.accessToken);
  }

  /// Decodes and checks if the cached JWT access token is expired (Priority 1 - Task 4).
  Future<bool> isTokenExpired() async {
    final token = await getAccessToken();
    if (token == null) return true;

    try {
      final parts = token.split('.');
      if (parts.length != 3) return true;

      // Base64Url decode the payload (second part of the JWT)
      var payload = parts[1];
      
      // Normalize base64 padding
      final padLength = (4 - (payload.length % 4)) % 4;
      payload += '=' * padLength;
      
      final decodedBytes = base64Url.decode(payload);
      final decodedString = utf8.decode(decodedBytes);
      final map = jsonDecode(decodedString) as Map<String, dynamic>;

      final exp = map['exp'] as int?;
      if (exp == null) return true;

      final expDateTime = DateTime.fromMillisecondsSinceEpoch(exp * 1000);
      // Return true if current time is past expiration (including a 10s buffer)
      return DateTime.now().add(const Duration(seconds: 10)).isAfter(expDateTime);
    } catch (_) {
      return true; // Fallback to expired if parsing fails
    }
  }

  /// Checks whether the user has a stored session.
  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: StorageKeys.accessToken);
    return token != null;
  }

  /// Returns the stored user info, or null if not logged in.
  Future<UserModel?> getStoredUser() async {
    final id = await _storage.read(key: StorageKeys.userId);
    final username = await _storage.read(key: StorageKeys.username);
    final email = await _storage.read(key: StorageKeys.email);
    final role = await _storage.read(key: StorageKeys.role);
    final location = await _storage.read(key: StorageKeys.location);

    if (id == null || username == null || email == null || role == null) {
      return null;
    }

    return UserModel(
      id: int.parse(id),
      username: username,
      email: email,
      role: role,
      location: location,
    );
  }

  /// Clears all stored tokens and user data.
  Future<void> logout() async {
    await _storage.deleteAll();
  }

  // ─── PRIVATE HELPERS ────────────────────────────────────

  /// Stores tokens and user info securely.
  Future<void> _storeSession({
    required String accessToken,
    required String refreshToken,
    required UserModel user,
  }) async {
    final futures = [
      _storage.write(key: StorageKeys.accessToken, value: accessToken),
      _storage.write(key: StorageKeys.refreshToken, value: refreshToken),
      _storage.write(key: StorageKeys.userId, value: user.id.toString()),
      _storage.write(key: StorageKeys.username, value: user.username),
      _storage.write(key: StorageKeys.email, value: user.email),
      _storage.write(key: StorageKeys.role, value: user.role),
    ];
    if (user.location != null) {
      futures.add(_storage.write(key: StorageKeys.location, value: user.location!));
    }
    await Future.wait(futures);
  }
}
