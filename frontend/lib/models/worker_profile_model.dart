import 'user_model.dart';
import 'worker_work_image_model.dart';

class WorkerProfileModel {
  final int id;
  final UserModel user;
  final String category;
  final double price;
  final String bio;
  final bool isOnline;
  final double rating;
  final int totalReviews;
  final int experienceYears;
  final String? coverImageUrl;
  final List<WorkerWorkImageModel> workImages;

  WorkerProfileModel({
    required this.id,
    required this.user,
    required this.category,
    required this.price,
    this.bio = '',
    required this.isOnline,
    required this.rating,
    required this.totalReviews,
    required this.experienceYears,
    this.coverImageUrl,
    this.workImages = const [],
  });

  factory WorkerProfileModel.fromJson(Map<String, dynamic> json) {
    final imagesJson = json['work_images'];
    final images = imagesJson is List
        ? imagesJson
              .map(
                (item) => WorkerWorkImageModel.fromJson(
                  item as Map<String, dynamic>,
                ),
              )
              .toList()
        : <WorkerWorkImageModel>[];

    return WorkerProfileModel(
      id: json['id'] as int,
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
      category: json['category'] as String,
      price: double.parse(json['price'].toString()),
      bio: json['bio'] as String? ?? '',
      isOnline: json['is_online'] as bool,
      rating: double.parse(json['rating'].toString()),
      totalReviews: json['total_reviews'] as int,
      experienceYears: json['experience_years'] as int,
      coverImageUrl: json['cover_image_url'] as String?,
      workImages: images,
    );
  }

  WorkerProfileModel copyWith({
    bool? isOnline,
    String? bio,
    List<WorkerWorkImageModel>? workImages,
  }) {
    return WorkerProfileModel(
      id: id,
      user: user,
      category: category,
      price: price,
      bio: bio ?? this.bio,
      isOnline: isOnline ?? this.isOnline,
      rating: rating,
      totalReviews: totalReviews,
      experienceYears: experienceYears,
      coverImageUrl: coverImageUrl,
      workImages: workImages ?? this.workImages,
    );
  }
}
