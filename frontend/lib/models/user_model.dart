import 'package:firebase_auth/firebase_auth.dart';

/// Represents an authenticated user from the backend.
class UserModel {
  final int id;
  final String username;
  final String email;
  final String role;
  final String? location;
  final String? phoneNumber;
  final String? profilePhotoUrl;

  const UserModel({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    this.location,
    this.phoneNumber,
    this.profilePhotoUrl,
  });

  /// Creates a [UserModel] from a signed-in Firebase user.
  factory UserModel.fromFirebaseUser(User user, {String role = 'customer'}) {
    return UserModel(
      id: user.uid.hashCode,
      username: user.displayName ?? user.phoneNumber ?? 'User',
      email: user.email ?? '${user.uid}@workersbridge.app',
      role: role,
      phoneNumber: user.phoneNumber,
      profilePhotoUrl: user.photoURL,
    );
  }

  /// Creates a [UserModel] from the API JSON response.
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as int,
      username: json['username'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
      location: json['location'] as String?,
      phoneNumber: json['phone_number'] as String?,
      profilePhotoUrl: json['profile_photo_url'] as String?,
    );
  }

  /// Converts this model to a JSON map.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'role': role,
      'location': location,
      'phone_number': phoneNumber,
      'profile_photo_url': profilePhotoUrl,
    };
  }

  UserModel copyWith({
    String? username,
    String? email,
    String? location,
    String? phoneNumber,
    String? profilePhotoUrl,
  }) {
    return UserModel(
      id: id,
      username: username ?? this.username,
      email: email ?? this.email,
      role: role,
      location: location ?? this.location,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      profilePhotoUrl: profilePhotoUrl ?? this.profilePhotoUrl,
    );
  }

  /// Whether this user has the worker role.
  bool get isWorker => role == 'worker';

  /// Whether this user has the customer role.
  bool get isCustomer => role == 'customer';

  /// Display-friendly role name.
  String get roleDisplay => role[0].toUpperCase() + role.substring(1);
}
