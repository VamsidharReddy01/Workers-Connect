import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';
import 'session_store.dart';

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
  final SessionStore _sessionStore = SessionStore();

  /// Sends a GET request.
  /// Automatically injects stored access token and retries once on 401 Unauthorized.
  Future<ApiResult> get(
    String url, {
    String? accessToken,
    bool isRetry = false,
  }) async {
    try {
      final headers = <String, String>{'Accept': 'application/json'};

      // 1. Fetch access token from storage if not explicitly provided
      var token = accessToken;
      if (!_isPublicAuthPost(url)) {
        token ??= await _sessionStore.getAccessToken();
      }

      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await _client
          .get(Uri.parse(url), headers: headers)
          .timeout(const Duration(seconds: 15));

      // 2. Intercept 401 Unauthorized and perform a Silent Refresh
      if (response.statusCode == 401 && !isRetry) {
        final refreshSuccess = await _attemptSilentRefresh();
        if (refreshSuccess) {
          // Retry original request with the new refreshed access token
          return get(url, isRetry: true);
        } else {
          return const ApiResult(
            success: false,
            errorMessage: 'Session expired. Please log in again.',
          );
        }
      }

      final decoded = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (decoded is List) {
          // Wrap list response in a map so ApiResult has consistent structure
          return ApiResult(success: true, data: {'list': decoded});
        }
        return ApiResult(success: true, data: decoded as Map<String, dynamic>);
      }

      // Handle 429 Too Many Requests (rate limiting)
      if (response.statusCode == 429) {
        return const ApiResult(
          success: false,
          errorMessage:
              'Too many attempts. Please wait a moment and try again.',
        );
      }

      // Fallback error message
      final message =
          decoded['detail'] ?? decoded['error'] ?? 'Something went wrong';
      return ApiResult(success: false, errorMessage: message.toString());
    } on SocketException {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url),
      );
    } on http.ClientException catch (e) {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url, detail: e.message),
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
        errorMessage: _connectionErrorMessage(url, detail: e.toString()),
      );
    }
  }

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
      token ??= await _sessionStore.getAccessToken();

      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await _client
          .post(Uri.parse(url), headers: headers, body: jsonEncode(body))
          .timeout(const Duration(seconds: 15));

      // 2. Intercept 401 Unauthorized and perform a Silent Refresh
      if (response.statusCode == 401 &&
          !isRetry &&
          url != ApiConstants.tokenRefreshEndpoint &&
          !_isPublicAuthPost(url)) {
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
          errorMessage:
              'Too many attempts. Please wait a moment and try again.',
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
      final message =
          responseData['detail'] ??
          responseData['error'] ??
          'Something went wrong';
      return ApiResult(success: false, errorMessage: message.toString());
    } on SocketException {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url),
      );
    } on http.ClientException catch (e) {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url, detail: e.message),
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
        errorMessage: _connectionErrorMessage(url, detail: e.toString()),
      );
    }
  }

  /// Sends a PATCH request with JSON body.
  /// Automatically injects stored access token and retries once on 401 Unauthorized.
  Future<ApiResult> patch(
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

      var token = accessToken;
      token ??= await _sessionStore.getAccessToken();

      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await _client
          .patch(Uri.parse(url), headers: headers, body: jsonEncode(body))
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 401 && !isRetry) {
        final refreshSuccess = await _attemptSilentRefresh();
        if (refreshSuccess) {
          return patch(url, body: body, isRetry: true);
        }
        return const ApiResult(
          success: false,
          errorMessage: 'Session expired. Please log in again.',
        );
      }

      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) {
        return const ApiResult(
          success: false,
          errorMessage: 'Unexpected response format from server.',
        );
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return ApiResult(success: true, data: decoded);
      }

      if (decoded.containsKey('errors')) {
        final errors = decoded['errors'];
        if (errors is Map<String, dynamic>) {
          return ApiResult(
            success: false,
            fieldErrors: errors,
            errorMessage: _extractFirstError(errors),
          );
        }
      }

      final message =
          decoded['detail'] ?? decoded['error'] ?? 'Something went wrong';
      return ApiResult(success: false, errorMessage: message.toString());
    } on SocketException {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url),
      );
    } on http.ClientException catch (e) {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url, detail: e.message),
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
        errorMessage: _connectionErrorMessage(url, detail: e.toString()),
      );
    }
  }

  String _connectionErrorMessage(String url, {String? detail}) {
    final backend = ApiConstants.serverBaseUrl;
    final portHint = url.contains(':5000')
        ? ' The app is using port 5000; Django defaults to port 8000 '
              '(run: python manage.py runserver).'
        : '';
    final detailSuffix = detail != null && detail.isNotEmpty
        ? ' ($detail)'
        : '';
    return 'Could not reach $url.$detailSuffix'
        '$portHint '
        'Backend should be at $backend — start it with '
        'python manage.py runserver in the backend folder.';
  }

  bool _isPublicAuthPost(String url) {
    return url == ApiConstants.loginEndpoint ||
        url == ApiConstants.signupEndpoint ||
        url == ApiConstants.sendSignupOtpEndpoint;
  }

  /// Attempts to perform a silent refresh behind the scenes when a 401 is hit.
  Future<bool> _attemptSilentRefresh() async {
    try {
      final refresh = await _sessionStore.getRefreshToken();
      if (refresh == null) return false;

      final headers = <String, String>{
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      final refreshResponse = await _client
          .post(
            Uri.parse(ApiConstants.tokenRefreshEndpoint),
            headers: headers,
            body: jsonEncode({'refresh': refresh}),
          )
          .timeout(const Duration(seconds: 10));

      if (refreshResponse.statusCode >= 200 &&
          refreshResponse.statusCode < 300) {
        final data = jsonDecode(refreshResponse.body) as Map<String, dynamic>;
        final newAccess = data['access'] as String;

        // Write the fresh token securely
        await _sessionStore.saveAccessToken(newAccess);
        return true;
      }
    } catch (_) {
      // Refresh failed
    }

    // Force wipe session storage as token is completely invalid/expired
    await _sessionStore.clear();
    return false;
  }

  /// Upload one or more files via multipart/form-data (e.g. portfolio images).
  Future<ApiResult> postMultipart(
    String url, {
    required List<http.MultipartFile> files,
    Map<String, String>? fields,
    bool isRetry = false,
  }) async {
    try {
      final request = http.MultipartRequest('POST', Uri.parse(url));
      request.headers['Accept'] = 'application/json';

      var token = await _sessionStore.getAccessToken();
      if (token != null) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      if (fields != null) {
        request.fields.addAll(fields);
      }
      request.files.addAll(files);

      final streamed = await request.send().timeout(
        const Duration(seconds: 60),
      );
      final response = await http.Response.fromStream(streamed);

      if (response.statusCode == 401 && !isRetry) {
        final refreshSuccess = await _attemptSilentRefresh();
        if (refreshSuccess) {
          return postMultipart(
            url,
            files: files,
            fields: fields,
            isRetry: true,
          );
        }
        return const ApiResult(
          success: false,
          errorMessage: 'Session expired. Please log in again.',
        );
      }

      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) {
        return const ApiResult(
          success: false,
          errorMessage: 'Unexpected response format from server.',
        );
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return ApiResult(success: true, data: decoded);
      }

      final message =
          decoded['error'] ??
          decoded['detail'] ??
          'Upload failed. Please try again.';
      return ApiResult(success: false, errorMessage: message.toString());
    } on SocketException {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url),
      );
    } on http.ClientException catch (e) {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url, detail: e.message),
      );
    } catch (e) {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url, detail: e.toString()),
      );
    }
  }

  /// Sends a DELETE request.
  Future<ApiResult> delete(String url, {bool isRetry = false}) async {
    try {
      final headers = <String, String>{'Accept': 'application/json'};
      var token = await _sessionStore.getAccessToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await _client
          .delete(Uri.parse(url), headers: headers)
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 401 && !isRetry) {
        final refreshSuccess = await _attemptSilentRefresh();
        if (refreshSuccess) {
          return delete(url, isRetry: true);
        }
        return const ApiResult(
          success: false,
          errorMessage: 'Session expired. Please log in again.',
        );
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return const ApiResult(success: true, data: null);
      }

      if (response.body.isEmpty) {
        return ApiResult(
          success: false,
          errorMessage: 'Delete failed (${response.statusCode}).',
        );
      }

      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) {
        final message =
            decoded['error'] ?? decoded['detail'] ?? 'Delete failed.';
        return ApiResult(success: false, errorMessage: message.toString());
      }
      return const ApiResult(success: false, errorMessage: 'Delete failed.');
    } on SocketException {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url),
      );
    } catch (e) {
      return ApiResult(
        success: false,
        errorMessage: _connectionErrorMessage(url, detail: e.toString()),
      );
    }
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
