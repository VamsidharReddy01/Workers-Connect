import 'package:flutter/material.dart';

import '../models/booking_model.dart';
import '../models/user_model.dart';
import '../services/booking_service.dart';
import '../utils/constants.dart';
import 'chat_screen.dart';

class BookingsScreen extends StatefulWidget {
  final UserModel user;

  const BookingsScreen({super.key, required this.user});

  @override
  State<BookingsScreen> createState() => BookingsScreenState();
}

class BookingsScreenState extends State<BookingsScreen> {
  final BookingService _bookingService = BookingService();
  List<BookingModel> _bookings = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() => _isLoading = true);
    final bookings = await _bookingService.getCustomerBookings();
    if (!mounted) return;
    setState(() {
      _bookings = bookings;
      _isLoading = false;
    });
  }

  Future<void> _openReviewDialog(BookingModel booking) async {
    int rating = 5;
    final feedbackController = TextEditingController();

    final submitted = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Rate your experience',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1E212D),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'How was ${booking.worker.user.username.replaceAll('_', ' ')}\'s ${booking.serviceCategory} service?',
                    style: const TextStyle(color: Color(0xFF6E7489)),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(5, (index) {
                      final star = index + 1;
                      return IconButton(
                        onPressed: () => setModalState(() => rating = star),
                        icon: Icon(
                          star <= rating
                              ? Icons.star_rounded
                              : Icons.star_outline_rounded,
                          color: const Color(0xFFFFA726),
                          size: 36,
                        ),
                      );
                    }),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: feedbackController,
                    maxLines: 4,
                    decoration: InputDecoration(
                      hintText: 'Share your feedback (optional)',
                      filled: true,
                      fillColor: const Color(0xFFF8FAFC),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: Color(0xFFE2E6F2)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(context, true),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.lightPrimary,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text(
                        'Submit Review',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );

    if (submitted != true || !mounted) {
      feedbackController.dispose();
      return;
    }

    final success = await _bookingService.submitReview(
      bookingId: booking.id,
      rating: rating,
      feedback: feedbackController.text,
    );
    feedbackController.dispose();
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          success
              ? 'Thank you for your feedback!'
              : (_bookingService.lastErrorMessage ??
                    'Could not submit review.'),
        ),
        backgroundColor: success ? AppColors.success : AppColors.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
    if (success) await refresh();
  }

  void _openChat(BookingModel booking) {
    final conversationId = booking.conversationId;
    if (conversationId == null) return;

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ChatScreen(
          currentUser: widget.user,
          conversationId: conversationId,
          title: booking.worker.user.username.replaceAll('_', ' '),
          subtitle: booking.serviceCategory,
        ),
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'completed':
        return AppColors.success;
      case 'cancelled':
      case 'declined':
        return AppColors.error;
      case 'requested':
        return AppColors.warning;
      default:
        return AppColors.lightPrimary;
    }
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
          'My Bookings',
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
            : _bookings.isEmpty
            ? ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  SizedBox(height: 120),
                  Icon(
                    Icons.calendar_month_outlined,
                    size: 64,
                    color: AppColors.lightPrimary,
                  ),
                  SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No Bookings Yet',
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
                      'Book a worker from Home and your appointments will appear here.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Color(0xFF6E7489)),
                    ),
                  ),
                ],
              )
            : ListView.separated(
                padding: const EdgeInsets.all(20),
                itemCount: _bookings.length,
                separatorBuilder: (_, __) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final booking = _bookings[index];
                  final workerName =
                      booking.worker.user.username.replaceAll('_', ' ');
                  return Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFFE2E6F2)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                workerName,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF1E212D),
                                ),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: _statusColor(booking.status)
                                    .withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text(
                                booking.statusDisplay,
                                style: TextStyle(
                                  color: _statusColor(booking.status),
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          booking.serviceCategory,
                          style: const TextStyle(
                            color: Color(0xFF6E7489),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '₹${booking.totalAmount.toStringAsFixed(0)} • ${_formatDate(booking.scheduledAt)}',
                          style: const TextStyle(
                            color: Color(0xFFA2A7B8),
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            if (booking.conversationId != null)
                              OutlinedButton.icon(
                                onPressed: () => _openChat(booking),
                                icon: const Icon(Icons.chat_bubble_outline, size: 18),
                                label: const Text('Chat'),
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: AppColors.lightPrimary,
                                ),
                              ),
                            if (booking.canReview) ...[
                              const SizedBox(width: 8),
                              ElevatedButton.icon(
                                onPressed: () => _openReviewDialog(booking),
                                icon: const Icon(Icons.star_outline, size: 18),
                                label: const Text('Rate'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.lightPrimary,
                                  foregroundColor: Colors.white,
                                ),
                              ),
                            ],
                            if (booking.isComplete && booking.hasReview)
                              const Padding(
                                padding: EdgeInsets.only(left: 8),
                                child: Row(
                                  children: [
                                    Icon(
                                      Icons.check_circle_outline,
                                      color: AppColors.success,
                                      size: 18,
                                    ),
                                    SizedBox(width: 4),
                                    Text(
                                      'Reviewed',
                                      style: TextStyle(
                                        color: AppColors.success,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        ),
                      ],
                    ),
                  );
                },
              ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}
