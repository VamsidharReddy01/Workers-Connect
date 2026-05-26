/// Represents an authenticated user from the backend.
class UserModel {
  final int id;
  final String username;
  final String email;
  final String role;
  final String? location;

  const UserModel({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    this.location,
  });

  /// Creates a [UserModel] from the API JSON response.
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as int,
      username: json['username'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
      location: json['location'] as String?,
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
    };
  }

  /// Whether this user has the worker role.
  bool get isWorker => role == 'worker';

  /// Whether this user has the customer role.
  bool get isCustomer => role == 'customer';

  /// Display-friendly role name.
  String get roleDisplay => role[0].toUpperCase() + role.substring(1);
}
