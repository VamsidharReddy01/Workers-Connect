import 'user_model.dart';
import 'worker_profile_model.dart';

class BookingModel {
  final int id;
  final UserModel customer;
  final WorkerProfileModel worker;
  final String serviceCategory;
  final String description;
  final String address;
  final DateTime scheduledAt;
  final double totalAmount;
  final String status;
  final String statusDisplay;
  final bool hasReview;
  final int? conversationId;
  final DateTime createdAt;
  final DateTime updatedAt;

  const BookingModel({
    required this.id,
    required this.customer,
    required this.worker,
    required this.serviceCategory,
    required this.description,
    required this.address,
    required this.scheduledAt,
    required this.totalAmount,
    required this.status,
    required this.statusDisplay,
    this.hasReview = false,
    this.conversationId,
    required this.createdAt,
    required this.updatedAt,
  });

  factory BookingModel.fromJson(Map<String, dynamic> json) {
    return BookingModel(
      id: json['id'] as int,
      customer: UserModel.fromJson(json['customer'] as Map<String, dynamic>),
      worker: WorkerProfileModel.fromJson(
        json['worker'] as Map<String, dynamic>,
      ),
      serviceCategory: json['service_category'] as String,
      description: json['description'] as String? ?? '',
      address: json['address'] as String,
      scheduledAt: DateTime.parse(json['scheduled_at'] as String).toLocal(),
      totalAmount: double.parse(json['total_amount'].toString()),
      status: json['status'] as String,
      statusDisplay:
          json['status_display'] as String? ?? json['status'] as String,
      hasReview: json['has_review'] as bool? ?? false,
      conversationId: json['conversation_id'] as int?,
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
      updatedAt: DateTime.parse(json['updated_at'] as String).toLocal(),
    );
  }

  bool get isPending => status == 'requested';
  bool get isActive =>
      status == 'accepted' || status == 'on_the_way' || status == 'in_progress';
  bool get isComplete => status == 'completed';
  bool get canReview => isComplete && !hasReview;
}

class WorkerDashboardMetrics {
  final int pendingRequests;
  final int activeJobs;
  final int completedJobs;
  final double totalEarnings;

  const WorkerDashboardMetrics({
    required this.pendingRequests,
    required this.activeJobs,
    required this.completedJobs,
    required this.totalEarnings,
  });

  factory WorkerDashboardMetrics.fromJson(Map<String, dynamic> json) {
    return WorkerDashboardMetrics(
      pendingRequests: json['pending_requests'] as int? ?? 0,
      activeJobs: json['active_jobs'] as int? ?? 0,
      completedJobs: json['completed_jobs'] as int? ?? 0,
      totalEarnings: double.parse((json['total_earnings'] ?? 0).toString()),
    );
  }
}

class WorkerDashboardData {
  final WorkerProfileModel profile;
  final WorkerDashboardMetrics metrics;

  const WorkerDashboardData({required this.profile, required this.metrics});

  factory WorkerDashboardData.fromJson(Map<String, dynamic> json) {
    return WorkerDashboardData(
      profile: WorkerProfileModel.fromJson(
        json['profile'] as Map<String, dynamic>,
      ),
      metrics: WorkerDashboardMetrics.fromJson(
        json['metrics'] as Map<String, dynamic>,
      ),
    );
  }
}
