import 'package:flutter/material.dart';

import '../models/booking_model.dart';
import '../models/user_model.dart';
import '../services/worker_service.dart';
import '../utils/constants.dart';
import 'chat_screen.dart';

class WorkerJobsScreen extends StatefulWidget {
  final UserModel user;

  const WorkerJobsScreen({super.key, required this.user});

  @override
  State<WorkerJobsScreen> createState() => WorkerJobsScreenState();
}

class WorkerJobsScreenState extends State<WorkerJobsScreen> {
  final WorkerService _workerService = WorkerService();
  List<BookingModel> _bookings = [];
  bool _isLoading = true;
  int? _updatingBookingId;
  String? _selectedStatus;

  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() => _isLoading = true);
    final bookings = await _workerService.getWorkerBookings(
      status: _selectedStatus,
    );
    if (!mounted) return;
    setState(() {
      _bookings = bookings;
      _isLoading = false;
    });
  }

  Future<void> _updateStatus(BookingModel booking, String status) async {
    setState(() => _updatingBookingId = booking.id);
    final updated = await _workerService.updateBookingStatus(
      bookingId: booking.id,
      status: status,
    );
    if (!mounted) return;
    setState(() => _updatingBookingId = null);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          updated == null ? 'Could not update booking.' : 'Booking updated.',
        ),
        backgroundColor: updated == null ? AppColors.error : AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
    if (updated != null) await refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 0,
        title: const Text(
          'Jobs & Bookings',
          style: TextStyle(
            color: Color(0xFF1E212D),
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
        child: Column(
          children: [
            _buildFilters(),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _bookings.isEmpty
                  ? ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: const [
                        SizedBox(height: 120),
                        Icon(
                          Icons.work_outline_rounded,
                          size: 60,
                          color: AppColors.lightPrimary,
                        ),
                        SizedBox(height: 14),
                        Center(
                          child: Text(
                            'No jobs found',
                            style: TextStyle(
                              color: Color(0xFF1E212D),
                              fontWeight: FontWeight.bold,
                              fontSize: 20,
                            ),
                          ),
                        ),
                      ],
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
                      itemCount: _bookings.length,
                      separatorBuilder: (context, index) =>
                          const SizedBox(height: 12),
                      itemBuilder: (context, index) =>
                          _buildBookingCard(_bookings[index]),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilters() {
    const options = <String?, String>{
      null: 'All',
      'requested': 'Requests',
      'accepted': 'Accepted',
      'on_the_way': 'On Way',
      'in_progress': 'Working',
      'completed': 'Done',
    };

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
      child: Row(
        children: options.entries.map((entry) {
          final selected = _selectedStatus == entry.key;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              selected: selected,
              label: Text(entry.value),
              selectedColor: AppColors.lightPrimary,
              backgroundColor: Colors.white,
              side: BorderSide(
                color: selected
                    ? AppColors.lightPrimary
                    : const Color(0xFFE2E6F2),
              ),
              labelStyle: TextStyle(
                color: selected ? Colors.white : const Color(0xFF6E7489),
                fontWeight: FontWeight.bold,
              ),
              onSelected: (_) async {
                setState(() => _selectedStatus = entry.key);
                await refresh();
              },
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildBookingCard(BookingModel booking) {
    final isUpdating = _updatingBookingId == booking.id;
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
                  booking.customer.username.replaceAll('_', ' '),
                  style: const TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              _statusPill(booking),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            booking.serviceCategory,
            style: const TextStyle(
              color: Color(0xFF6E7489),
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '${booking.address} • Rs. ${booking.totalAmount.toStringAsFixed(0)}',
            style: const TextStyle(color: Color(0xFFA2A7B8), fontSize: 12),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              if (booking.conversationId != null)
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => ChatScreen(
                          currentUser: widget.user,
                          conversationId: booking.conversationId!,
                          title: booking.customer.username.replaceAll('_', ' '),
                          subtitle: booking.serviceCategory,
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.chat_bubble_outline, size: 18),
                  label: const Text('Chat'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.lightPrimary,
                  ),
                ),
              const Spacer(),
              if (isUpdating)
                const SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              else
                ..._actions(booking),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statusPill(BookingModel booking) {
    final color = switch (booking.status) {
      'completed' => AppColors.success,
      'declined' || 'cancelled' => AppColors.error,
      'requested' => AppColors.warning,
      _ => AppColors.lightPrimary,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        booking.statusDisplay,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  List<Widget> _actions(BookingModel booking) {
    switch (booking.status) {
      case 'requested':
        return [
          TextButton(
            onPressed: () => _updateStatus(booking, 'declined'),
            child: const Text('Decline'),
          ),
          ElevatedButton(
            onPressed: () => _updateStatus(booking, 'accepted'),
            child: const Text('Accept'),
          ),
        ];
      case 'accepted':
        return [
          ElevatedButton(
            onPressed: () => _updateStatus(booking, 'on_the_way'),
            child: const Text('On Way'),
          ),
        ];
      case 'on_the_way':
        return [
          ElevatedButton(
            onPressed: () => _updateStatus(booking, 'in_progress'),
            child: const Text('Start'),
          ),
        ];
      case 'in_progress':
        return [
          ElevatedButton(
            onPressed: () => _updateStatus(booking, 'completed'),
            child: const Text('Complete'),
          ),
        ];
      default:
        return [];
    }
  }
}
