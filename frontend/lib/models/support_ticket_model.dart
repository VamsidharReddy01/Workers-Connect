class SupportTicketModel {
  final int id;
  final String subject;
  final String message;
  final String status;
  final String statusDisplay;
  final String adminNote;
  final DateTime createdAt;
  final DateTime updatedAt;

  const SupportTicketModel({
    required this.id,
    required this.subject,
    required this.message,
    required this.status,
    required this.statusDisplay,
    required this.adminNote,
    required this.createdAt,
    required this.updatedAt,
  });

  factory SupportTicketModel.fromJson(Map<String, dynamic> json) {
    return SupportTicketModel(
      id: json['id'] as int,
      subject: json['subject'] as String,
      message: json['message'] as String,
      status: json['status'] as String,
      statusDisplay:
          json['status_display'] as String? ?? json['status'] as String,
      adminNote: json['admin_note'] as String? ?? '',
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
      updatedAt: DateTime.parse(json['updated_at'] as String).toLocal(),
    );
  }
}
