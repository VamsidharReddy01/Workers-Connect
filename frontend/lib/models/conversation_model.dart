import 'user_model.dart';

class MessageModel {
  final int id;
  final UserModel sender;
  final String text;
  final DateTime createdAt;
  final bool isRead;

  MessageModel({
    required this.id,
    required this.sender,
    required this.text,
    required this.createdAt,
    required this.isRead,
  });

  factory MessageModel.fromJson(Map<String, dynamic> json) {
    return MessageModel(
      id: json['id'] as int,
      sender: UserModel.fromJson(json['sender'] as Map<String, dynamic>),
      text: json['text'] as String,
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
      isRead: json['is_read'] as bool? ?? false,
    );
  }
}

class ConversationModel {
  final int id;
  final String otherPartyName;
  final int unreadCount;
  final MessageModel? lastMessage;
  final int? bookingId;
  final String? serviceCategory;
  final String? bookingStatus;
  final DateTime updatedAt;

  ConversationModel({
    required this.id,
    required this.otherPartyName,
    required this.unreadCount,
    this.lastMessage,
    this.bookingId,
    this.serviceCategory,
    this.bookingStatus,
    required this.updatedAt,
  });

  factory ConversationModel.fromJson(Map<String, dynamic> json) {
    final booking = json['booking'] as Map<String, dynamic>?;
    final lastRaw = json['last_message'];
    return ConversationModel(
      id: json['id'] as int,
      otherPartyName: json['other_party_name'] as String? ?? 'Chat',
      unreadCount: json['unread_count'] as int? ?? 0,
      lastMessage: lastRaw is Map<String, dynamic>
          ? MessageModel.fromJson(lastRaw)
          : null,
      bookingId: booking?['id'] as int?,
      serviceCategory: booking?['service_category'] as String?,
      bookingStatus: booking?['status'] as String?,
      updatedAt: DateTime.parse(json['updated_at'] as String).toLocal(),
    );
  }
}
