import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/user_model.dart';
import '../utils/constants.dart';

class SessionStore {
  static final SessionStore _instance = SessionStore._internal();
  factory SessionStore() => _instance;
  SessionStore._internal();

  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  String? _accessToken;
  String? _refreshToken;
  UserModel? _user;

  Future<String?> getAccessToken() async {
    if (_accessToken != null) return _accessToken;
    try {
      _accessToken = await _storage.read(key: StorageKeys.accessToken);
      return _accessToken;
    } catch (_) {
      return null;
    }
  }

  Future<String?> getRefreshToken() async {
    if (_refreshToken != null) return _refreshToken;
    try {
      _refreshToken = await _storage.read(key: StorageKeys.refreshToken);
      return _refreshToken;
    } catch (_) {
      return null;
    }
  }

  Future<UserModel?> getUser() async {
    if (_user != null) return _user;
    try {
      final id = await _storage.read(key: StorageKeys.userId);
      final username = await _storage.read(key: StorageKeys.username);
      final email = await _storage.read(key: StorageKeys.email);
      final role = await _storage.read(key: StorageKeys.role);
      final location = await _storage.read(key: StorageKeys.location);

      if (id == null || username == null || email == null || role == null) {
        return null;
      }

      _user = UserModel(
        id: int.parse(id),
        username: username,
        email: email,
        role: role,
        location: location,
      );
      return _user;
    } catch (_) {
      return null;
    }
  }

  Future<void> saveSession({
    required String accessToken,
    required String refreshToken,
    required UserModel user,
  }) async {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    _user = user;

    try {
      await Future.wait([
        _storage.write(key: StorageKeys.accessToken, value: accessToken),
        _storage.write(key: StorageKeys.refreshToken, value: refreshToken),
        _storage.write(key: StorageKeys.userId, value: user.id.toString()),
        _storage.write(key: StorageKeys.username, value: user.username),
        _storage.write(key: StorageKeys.email, value: user.email),
        _storage.write(key: StorageKeys.role, value: user.role),
        if (user.location != null)
          _storage.write(key: StorageKeys.location, value: user.location!),
      ]);
    } catch (_) {
      // Web secure storage can fail in some local browser contexts. Keep the
      // in-memory session so the current run continues to work.
    }
  }

  Future<void> saveAccessToken(String accessToken) async {
    _accessToken = accessToken;
    try {
      await _storage.write(key: StorageKeys.accessToken, value: accessToken);
    } catch (_) {}
  }

  Future<void> clear() async {
    _accessToken = null;
    _refreshToken = null;
    _user = null;
    try {
      await _storage.deleteAll();
    } catch (_) {}
  }
}
