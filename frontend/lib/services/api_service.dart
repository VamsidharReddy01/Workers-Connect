import 'dart:convert';
import 'dart:io';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';

/// Result wrapper for API calls.
class ApiResult {
  final bool success;
  final Map<String, dynamic>? data;
  final String? errorMessage;
  final Map<String, dynamic>? fieldErrors;

  const ApiResult({
    required this.success,
    this.data,
    this.errorMessage,
    this.fieldErrors,
  });
}

/// Low-level HTTP client for communicating with the Django backend.
/// Automatically handles JWT injection, 401 interception, silent refreshes, and retries.
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final http.Client _client = http.Client();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  /// Sends a POST request with JSON body.
  /// Automatically injects stored access token and retries once on 401 Unauthorized.
  Future<ApiResult> post(
    String url, {
    required Map<String, dynamic> body,
    String? accessToken,
    bool isRetry = false,
  }) async {
    try {
      final headers = <String, String>{
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      // 1. Fetch access token from storage if not explicitly provided
      var token = accessToken;
      if (token == null) {
        token = await _storage.read(key: StorageKeys.accessToken);
      }

      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await _client
          .post(
            Uri.parse(url),
            headers: headers,
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 15));

      // 2. Intercept 401 Unauthorized and perform a Silent Refresh
      if (response.statusCode == 401 && !isRetry && url != ApiConstants.tokenRefreshEndpoint && url != ApiConstants.loginEndpoint) {
        final refreshSuccess = await _attemptSilentRefresh();
        if (refreshSuccess) {
          // Retry original request with the new refreshed access token
          return post(url, body: body, isRetry: true);
        } else {
          return const ApiResult(
            success: false,
            errorMessage: 'Session expired. Please log in again.',
          );
        }
      }

      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) {
        return const ApiResult(
          success: false,
          errorMessage: 'Unexpected response format from server.',
        );
      }
      final responseData = decoded;

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return ApiResult(success: true, data: responseData);
      }

      // Handle 429 Too Many Requests (rate limiting)
      if (response.statusCode == 429) {
        return const ApiResult(
          success: false,
          errorMessage: 'Too many attempts. Please wait a moment and try again.',
        );
      }

      // Parse field-level errors from DRF
      if (responseData.containsKey('errors')) {
        final errors = responseData['errors'];
        if (errors is Map<String, dynamic>) {
          return ApiResult(
            success: false,
            fieldErrors: errors,
            errorMessage: _extractFirstError(errors),
          );
        }
      }

      // Fallback error message
      final message = responseData['detail'] ??
          responseData['error'] ??
          'Something went wrong';
      return ApiResult(success: false, errorMessage: message.toString());
    } on SocketException {
      return const ApiResult(
        success: false,
        errorMessage: 'No internet connection. Please check your network.',
      );
    } on HttpException {
      return const ApiResult(
        success: false,
        errorMessage: 'Server error. Please try again later.',
      );
    } on FormatException {
      return const ApiResult(
        success: false,
        errorMessage: 'Unexpected response from server.',
      );
    } catch (e) {
      return ApiResult(
        success: false,
        errorMessage: 'Connection failed. Is the server running?',
      );
    }
  }

  /// Attempts to perform a silent refresh behind the scenes when a 401 is hit.
  Future<bool> _attemptSilentRefresh() async {
    try {
      final refresh = await _storage.read(key: StorageKeys.refreshToken);
      if (refresh == null) return false;

      final headers = <String, String>{
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      final refreshResponse = await _client.post(
        Uri.parse(ApiConstants.tokenRefreshEndpoint),
        headers: headers,
        body: jsonEncode({'refresh': refresh}),
      ).timeout(const Duration(seconds: 10));

      if (refreshResponse.statusCode >= 200 && refreshResponse.statusCode < 300) {
        final data = jsonDecode(refreshResponse.body) as Map<String, dynamic>;
        final newAccess = data['access'] as String;
        
        // Write the fresh token securely
        await _storage.write(key: StorageKeys.accessToken, value: newAccess);
        return true;
      }
    } catch (_) {
      // Refresh failed
    }

    // Force wipe session storage as token is completely invalid/expired
    await _storage.deleteAll();
    return false;
  }

  /// Extracts the first error message from a DRF error map.
  String _extractFirstError(Map<String, dynamic> errors) {
    for (final entry in errors.entries) {
      final value = entry.value;
      if (value is List && value.isNotEmpty) {
        return value.first.toString();
      }
      if (value is String) {
        return value;
      }
      if (value is Map) {
        for (final inner in value.values) {
          if (inner is List && inner.isNotEmpty) return inner.first.toString();
          if (inner is String) return inner;
        }
      }
    }
    return 'Validation failed. Please check your input.';
  }
}
