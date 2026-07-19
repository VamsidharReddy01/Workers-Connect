import 'package:flutter/material.dart';

import '../models/conversation_model.dart';
import '../models/user_model.dart';
import '../services/booking_service.dart';
import '../utils/constants.dart';
import 'chat_screen.dart';

class MessagesScreen extends StatefulWidget {
  final UserModel user;

  const MessagesScreen({super.key, required this.user});

  @override
  State<MessagesScreen> createState() => MessagesScreenState();
}

class MessagesScreenState extends State<MessagesScreen> {
  final ChatService _chatService = ChatService();
  List<ConversationModel> _conversations = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() => _isLoading = true);
    final conversations = await _chatService.getConversations();
    if (!mounted) return;
    setState(() {
      _conversations = conversations;
      _isLoading = false;
    });
  }

  void _openChat(ConversationModel conversation) {
    Navigator.of(context)
        .push(
          MaterialPageRoute(
            builder: (_) => ChatScreen(
              currentUser: widget.user,
              conversationId: conversation.id,
              title: conversation.otherPartyName,
              subtitle: conversation.serviceCategory,
            ),
          ),
        )
        .then((_) => refresh());
  }

  String _formatTime(DateTime dateTime) {
    final now = DateTime.now();
    if (now.difference(dateTime).inDays == 0) {
      final hour = dateTime.hour.toString().padLeft(2, '0');
      final minute = dateTime.minute.toString().padLeft(2, '0');
      return '$hour:$minute';
    }
    return '${dateTime.day}/${dateTime.month}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.white,
        title: const Text(
          'Chats',
          style: TextStyle(
            color: Color(0xFF1E212D),
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFFE2E6F2), height: 1),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: refresh,
        color: AppColors.lightPrimary,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator(strokeWidth: 2.5))
            : _conversations.isEmpty
            ? ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  SizedBox(height: 120),
                  Icon(
                    Icons.chat_bubble_outline_rounded,
                    size: 64,
                    color: AppColors.lightPrimary,
                  ),
                  SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No Messages Yet',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1E212D),
                      ),
                    ),
                  ),
                  SizedBox(height: 8),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 32),
                    child: Text(
                      'When you book a worker, a chat thread opens automatically here.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Color(0xFF6E7489)),
                    ),
                  ),
                ],
              )
            : ListView.separated(
                padding: const EdgeInsets.symmetric(vertical: 8),
                itemCount: _conversations.length,
                separatorBuilder: (_, __) => const Divider(
                  height: 1,
                  indent: 76,
                  color: Color(0xFFE2E6F2),
                ),
                itemBuilder: (context, index) {
                  final conversation = _conversations[index];
                  final last = conversation.lastMessage;
                  return ListTile(
                    onTap: () => _openChat(conversation),
                    leading: CircleAvatar(
                      backgroundColor: AppColors.lightPrimary.withValues(
                        alpha: 0.1,
                      ),
                      child: Text(
                        conversation.otherPartyName.isNotEmpty
                            ? conversation.otherPartyName[0].toUpperCase()
                            : '?',
                        style: const TextStyle(
                          color: AppColors.lightPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    title: Text(
                      conversation.otherPartyName,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1E212D),
                      ),
                    ),
                    subtitle: Text(
                      last?.text ?? 'No messages yet',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: Color(0xFF6E7489)),
                    ),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          _formatTime(conversation.updatedAt),
                          style: const TextStyle(
                            fontSize: 11,
                            color: Color(0xFFA2A7B8),
                          ),
                        ),
                        if (conversation.unreadCount > 0) ...[
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.lightPrimary,
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(
                              '${conversation.unreadCount}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                },
              ),
      ),
    );
  }
}
