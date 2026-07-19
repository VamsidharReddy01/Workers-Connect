import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'api_service.dart';
import '../models/booking_model.dart';
import '../models/category_model.dart';
import '../models/worker_profile_model.dart';
import '../models/worker_work_image_model.dart';
import '../utils/constants.dart';

class PortfolioUploadFile {
  final String filename;
  final Uint8List bytes;

  const PortfolioUploadFile({required this.filename, required this.bytes});
}

class WorkerService {
  static final WorkerService _instance = WorkerService._internal();
  factory WorkerService() => _instance;
  WorkerService._internal();

  final ApiService _api = ApiService();

  String? lastErrorMessage;

  Future<List<String>> getJobCategoryOptions() async {
    final result = await _api.get(ApiConstants.jobCategoriesEndpoint);
    if (result.success && result.data != null) {
      final list = result.data!['list'];
      if (list is List) {
        return list.map((e) => e.toString()).toList();
      }
    }
    return [];
  }

  Future<List<CategoryModel>> getCategories() async {
    final result = await _api.get(ApiConstants.categoriesEndpoint);
    if (result.success && result.data != null) {
      final list = result.data!['list'];
      if (list is List) {
        return list
            .map((item) => CategoryModel.fromJson(item as Map<String, dynamic>))
            .toList();
      }
    }
    return [];
  }

  Future<List<WorkerProfileModel>> getNearbyWorkers({
    String? category,
    String? search,
  }) async {
    var url = ApiConstants.nearbyWorkersEndpoint;
    final params = <String>[];
    if (category != null && category.isNotEmpty) {
      params.add('category=${Uri.encodeComponent(category)}');
    }
    if (search != null && search.isNotEmpty) {
      params.add('search=${Uri.encodeComponent(search)}');
    }
    if (params.isNotEmpty) {
      url += '?${params.join('&')}';
    }

    final result = await _api.get(url);
    if (result.success && result.data != null) {
      final list = result.data!['list'] as List;
      return list
          .map(
            (item) => WorkerProfileModel.fromJson(item as Map<String, dynamic>),
          )
          .toList();
    }
    return [];
  }

  Future<WorkerProfileModel?> getWorkerDetail(int workerId) async {
    final result = await _api.get(ApiConstants.workerDetailEndpoint(workerId));
    if (result.success && result.data != null) {
      return WorkerProfileModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }

  Future<WorkerProfileModel?> getOwnProfile() async {
    final result = await _api.get(ApiConstants.workerProfileEndpoint);
    if (result.success && result.data != null) {
      return WorkerProfileModel.fromJson(result.data!);
    }
    return null;
  }

  Future<WorkerProfileModel?> saveProfile({
    required String category,
    required double price,
    required int experienceYears,
    String bio = '',
    bool isOnline = true,
  }) async {
    lastErrorMessage = null;
    final result = await _api.post(
      ApiConstants.workerProfileEndpoint,
      body: {
        'category': category.trim(),
        'price': price,
        'experience_years': experienceYears,
        'bio': bio.trim(),
        'is_online': isOnline,
      },
    );
    if (result.success && result.data != null) {
      return WorkerProfileModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }

  Future<WorkerProfileModel?> updateProfile({
    required String category,
    required double price,
    required int experienceYears,
    String bio = '',
    bool? isOnline,
  }) async {
    lastErrorMessage = null;
    final body = <String, dynamic>{
      'category': category.trim(),
      'price': price,
      'experience_years': experienceYears,
      'bio': bio.trim(),
    };
    if (isOnline != null) {
      body['is_online'] = isOnline;
    }

    final result = await _api.patch(
      ApiConstants.workerProfileEndpoint,
      body: body,
    );
    if (result.success && result.data != null) {
      return WorkerProfileModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }

  Future<List<WorkerWorkImageModel>> uploadWorkImages(
    List<PortfolioUploadFile> files,
  ) async {
    lastErrorMessage = null;
    if (files.isEmpty) return [];

    final multipartFiles = files
        .map(
          (file) => http.MultipartFile.fromBytes(
            'images',
            file.bytes,
            filename: file.filename,
          ),
        )
        .toList();

    final result = await _api.postMultipart(
      ApiConstants.workerWorkImagesEndpoint,
      files: multipartFiles,
    );

    if (result.success && result.data != null) {
      final list = result.data!['list'];
      if (list is List) {
        return list
            .map(
              (item) =>
                  WorkerWorkImageModel.fromJson(item as Map<String, dynamic>),
            )
            .toList();
      }
    }

    lastErrorMessage = result.errorMessage;
    return [];
  }

  Future<bool> deleteWorkImage(int imageId) async {
    lastErrorMessage = null;
    final result = await _api.delete(
      ApiConstants.workerWorkImageDeleteEndpoint(imageId),
    );
    if (result.success) return true;
    lastErrorMessage = result.errorMessage;
    return false;
  }

  Future<WorkerProfileModel?> updateAvailability(bool isOnline) async {
    final result = await _api.patch(
      ApiConstants.workerAvailabilityEndpoint,
      body: {'is_online': isOnline},
    );
    if (result.success && result.data != null) {
      return WorkerProfileModel.fromJson(result.data!);
    }
    return null;
  }

  Future<WorkerDashboardData?> getWorkerDashboard() async {
    final result = await _api.get(ApiConstants.workerDashboardEndpoint);
    if (result.success && result.data != null) {
      return WorkerDashboardData.fromJson(result.data!);
    }
    return null;
  }

  Future<List<BookingModel>> getWorkerBookings({String? status}) async {
    var url = ApiConstants.workerBookingsEndpoint;
    if (status != null && status.isNotEmpty) {
      url += '?status=${Uri.encodeComponent(status)}';
    }

    final result = await _api.get(url);
    if (result.success && result.data != null) {
      final list = result.data!['list'] as List;
      return list
          .map((item) => BookingModel.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  Future<BookingModel?> updateBookingStatus({
    required int bookingId,
    required String status,
  }) async {
    final result = await _api.patch(
      ApiConstants.workerBookingStatusEndpoint(bookingId),
      body: {'status': status},
    );
    if (result.success && result.data != null) {
      return BookingModel.fromJson(result.data!);
    }
    return null;
  }

  Future<BookingModel?> createBooking({
    required int workerId,
    required String serviceCategory,
    required String address,
    required DateTime scheduledAt,
    required double totalAmount,
    String description = '',
  }) async {
    final result = await _api.post(
      ApiConstants.customerBookingCreateEndpoint,
      body: {
        'worker_id': workerId,
        'service_category': serviceCategory,
        'address': address,
        'scheduled_at': scheduledAt.toUtc().toIso8601String(),
        'total_amount': totalAmount,
        'description': description,
      },
    );
    if (result.success && result.data != null) {
      return BookingModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }
}
