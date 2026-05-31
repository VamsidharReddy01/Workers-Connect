import 'api_service.dart';
import '../models/booking_model.dart';
import '../models/conversation_model.dart';
import '../utils/constants.dart';

class BookingService {
  static final BookingService _instance = BookingService._internal();
  factory BookingService() => _instance;
  BookingService._internal();

  final ApiService _api = ApiService();
  String? lastErrorMessage;

  Future<List<BookingModel>> getCustomerBookings({String? status}) async {
    var url = ApiConstants.customerBookingsEndpoint;
    if (status != null && status.isNotEmpty) {
      url += '?status=${Uri.encodeComponent(status)}';
    }

    final result = await _api.get(url);
    if (result.success && result.data != null) {
      final list = result.data!['list'];
      if (list is List) {
        return list
            .map((item) => BookingModel.fromJson(item as Map<String, dynamic>))
            .toList();
      }
    }
    lastErrorMessage = result.errorMessage;
    return [];
  }

  Future<bool> submitReview({
    required int bookingId,
    required int rating,
    String feedback = '',
  }) async {
    lastErrorMessage = null;
    final result = await _api.post(
      ApiConstants.bookingReviewEndpoint(bookingId),
      body: {
        'rating': rating,
        'feedback': feedback.trim(),
      },
    );
    if (result.success) return true;
    lastErrorMessage = result.errorMessage;
    return false;
  }
}

class ChatService {
  static final ChatService _instance = ChatService._internal();
  factory ChatService() => _instance;
  ChatService._internal();

  final ApiService _api = ApiService();
  String? lastErrorMessage;

  Future<List<ConversationModel>> getConversations() async {
    final result = await _api.get(ApiConstants.conversationsEndpoint);
    if (result.success && result.data != null) {
      final list = result.data!['list'];
      if (list is List) {
        return list
            .map(
              (item) => ConversationModel.fromJson(item as Map<String, dynamic>),
            )
            .toList();
      }
    }
    lastErrorMessage = result.errorMessage;
    return [];
  }

  Future<List<MessageModel>> getMessages(int conversationId) async {
    final result = await _api.get(
      ApiConstants.conversationMessagesEndpoint(conversationId),
    );
    if (result.success && result.data != null) {
      final list = result.data!['list'];
      if (list is List) {
        return list
            .map((item) => MessageModel.fromJson(item as Map<String, dynamic>))
            .toList();
      }
    }
    lastErrorMessage = result.errorMessage;
    return [];
  }

  Future<MessageModel?> sendMessage({
    required int conversationId,
    required String text,
  }) async {
    lastErrorMessage = null;
    final result = await _api.post(
      ApiConstants.conversationMessagesEndpoint(conversationId),
      body: {'text': text.trim()},
    );
    if (result.success && result.data != null) {
      return MessageModel.fromJson(result.data!);
    }
    lastErrorMessage = result.errorMessage;
    return null;
  }
}
