import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../models/support_ticket_model.dart';
import '../models/user_model.dart';
import '../utils/constants.dart';
import 'api_service.dart';

class ProfilePhotoUpload {
  final String filename;
  final Uint8List bytes;

  const ProfilePhotoUpload({required this.filename, required this.bytes});
}

class ProfileService {
  static final ProfileService _instance = ProfileService._internal();
  factory ProfileService() => _instance;
  ProfileService._internal();

  final ApiService _api = ApiService();
  String? lastErrorMessage;

  Future<UserModel?> getProfile() async {
    lastErrorMessage = null;
    final result = await _api.get(ApiConstants.userProfileEndpoint);
    if (result.success && result.data != null) {
      return UserModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }

  Future<UserModel?> updateProfile({
    required String username,
    required String email,
    required String phoneNumber,
    required String location,
    ProfilePhotoUpload? photo,
  }) async {
    lastErrorMessage = null;
    final fields = <String, String>{
      'username': username.trim(),
      'email': email.trim().toLowerCase(),
      'phone_number': phoneNumber.trim(),
      'location': location.trim(),
    };

    final files = <http.MultipartFile>[];
    if (photo != null) {
      files.add(
        http.MultipartFile.fromBytes(
          'profile_photo',
          photo.bytes,
          filename: photo.filename,
        ),
      );
    }

    final result = await _api.patchMultipart(
      ApiConstants.userProfileEndpoint,
      fields: fields,
      files: files,
    );
    if (result.success && result.data != null) {
      return UserModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }

  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
    required String confirmPassword,
  }) async {
    lastErrorMessage = null;
    final result = await _api.post(
      ApiConstants.changePasswordEndpoint,
      body: {
        'old_password': oldPassword,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      },
    );
    if (result.success) return true;
    lastErrorMessage = result.errorMessage;
    return false;
  }

  Future<List<SupportTicketModel>> getSupportTickets() async {
    lastErrorMessage = null;
    final result = await _api.get(ApiConstants.supportTicketsEndpoint);
    if (result.success && result.data != null) {
      final list = result.data!['list'];
      if (list is List) {
        return list
            .map(
              (item) =>
                  SupportTicketModel.fromJson(item as Map<String, dynamic>),
            )
            .toList();
      }
    }
    lastErrorMessage = result.errorMessage;
    return [];
  }

  Future<SupportTicketModel?> submitTicket({
    required String subject,
    required String message,
  }) async {
    lastErrorMessage = null;
    final result = await _api.post(
      ApiConstants.supportTicketsEndpoint,
      body: {'subject': subject.trim(), 'message': message.trim()},
    );
    if (result.success && result.data != null) {
      return SupportTicketModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }
}
