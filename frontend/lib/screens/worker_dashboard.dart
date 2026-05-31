import 'package:flutter/material.dart';

import '../models/booking_model.dart';
import '../models/user_model.dart';
import '../models/worker_profile_model.dart';
import '../services/auth_service.dart';
import '../services/booking_service.dart';
import '../services/worker_service.dart';
import '../utils/constants.dart';
import 'chat_screen.dart';
import 'login_screen.dart';
import 'worker_profile_setup_screen.dart';

class WorkerDashboard extends StatefulWidget {
  final UserModel user;

  const WorkerDashboard({super.key, required this.user});

  @override
  State<WorkerDashboard> createState() => _WorkerDashboardState();
}

class _WorkerDashboardState extends State<WorkerDashboard> {
  final WorkerService _workerService = WorkerService();

  WorkerProfileModel? _profile;
  WorkerDashboardMetrics _metrics = const WorkerDashboardMetrics(
    pendingRequests: 0,
    activeJobs: 0,
    completedJobs: 0,
    totalEarnings: 0,
  );
  List<BookingModel> _bookings = [];
  String _selectedFilter = 'all';
  bool _isLoading = true;
  bool _isUpdatingAvailability = false;
  int? _updatingBookingId;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final dashboard = await _workerService.getWorkerDashboard();
    if (!mounted) return;

    if (dashboard == null) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => WorkerProfileSetupScreen(user: widget.user),
        ),
      );
      return;
    }

    final bookings = await _workerService.getWorkerBookings(
      status: _selectedFilter == 'all' ? null : _selectedFilter,
    );
    if (!mounted) return;

    setState(() {
      _profile = dashboard.profile;
      _metrics = dashboard.metrics;
      _bookings = bookings;
      _isLoading = false;
    });
  }

  Future<void> _setAvailability(bool isOnline) async {
    if (_profile == null || _isUpdatingAvailability) return;

    setState(() {
      _isUpdatingAvailability = true;
      _profile = _profile!.copyWith(isOnline: isOnline);
    });

    final updated = await _workerService.updateAvailability(isOnline);
    if (!mounted) return;

    setState(() {
      _isUpdatingAvailability = false;
      if (updated != null) {
        _profile = updated;
      }
    });

    if (updated == null) {
      _showSnack(
        'Could not update availability. Please try again.',
        isError: true,
      );
      await _loadDashboard();
    }
  }

  Future<void> _updateBookingStatus(BookingModel booking, String status) async {
    setState(() {
      _updatingBookingId = booking.id;
    });

    final updated = await _workerService.updateBookingStatus(
      bookingId: booking.id,
      status: status,
    );
    if (!mounted) return;

    setState(() {
      _updatingBookingId = null;
    });

    if (updated == null) {
      _showSnack('Could not update this booking.', isError: true);
      return;
    }

    _showSnack('Booking marked as ${updated.statusDisplay}.');
    await _loadDashboard();
  }

  Future<void> _handleLogout() async {
    final shouldLogout = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text(
          'Logout',
          style: TextStyle(
            color: Color(0xFF1E212D),
            fontWeight: FontWeight.bold,
          ),
        ),
        content: const Text(
          'Are you sure you want to end your worker session?',
          style: TextStyle(color: Color(0xFF6E7489)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text(
              'Cancel',
              style: TextStyle(color: Color(0xFFA2A7B8)),
            ),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text(
              'Logout',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );

    if (shouldLogout != true) return;

    await AuthService().logout();
    if (!mounted) return;

    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  void _showSnack(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? AppColors.error : AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: Color(0xFFF8FAFC),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: AppColors.lightPrimary),
              SizedBox(height: 16),
              Text(
                'Loading worker workspace...',
                style: TextStyle(
                  color: Color(0xFF6E7489),
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.lightPrimary,
          onRefresh: _loadDashboard,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(
              parent: BouncingScrollPhysics(),
            ),
            slivers: [
              SliverToBoxAdapter(child: _buildHeader()),
              SliverToBoxAdapter(child: _buildProfileCard()),
              SliverToBoxAdapter(child: _buildMetrics()),
              SliverToBoxAdapter(child: _buildFilters()),
              if (_errorMessage != null)
                SliverToBoxAdapter(child: _buildErrorState(_errorMessage!))
              else if (_bookings.isEmpty)
                SliverToBoxAdapter(child: _buildEmptyState())
              else
                SliverList.separated(
                  itemCount: _bookings.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(height: 12),
                  itemBuilder: (context, index) => Padding(
                    padding: EdgeInsets.fromLTRB(
                      20,
                      index == 0 ? 0 : 0,
                      20,
                      index == _bookings.length - 1 ? 32 : 0,
                    ),
                    child: _buildBookingCard(_bookings[index]),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 12, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: AppColors.buttonGradient,
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.accentViolet.withOpacity(0.2),
                          blurRadius: 8,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.connect_without_contact,
                      size: 20,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Workers Connect',
                    style: TextStyle(
                      color: Color(0xFF1E212D),
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.3,
                    ),
                  ),
                ],
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    tooltip: 'Edit profile',
                    onPressed: _profile == null
                        ? null
                        : () async {
                            final updated = await Navigator.of(context).push<bool>(
                              MaterialPageRoute(
                                builder: (_) => WorkerProfileSetupScreen(
                                  user: widget.user,
                                  existingProfile: _profile,
                                  isEditing: true,
                                ),
                              ),
                            );
                            if (updated == true) {
                              await _loadDashboard();
                            }
                          },
                    icon: const Icon(Icons.edit_outlined, color: Color(0xFF1E212D)),
                  ),
                  IconButton(
                    tooltip: 'Logout',
                    onPressed: _handleLogout,
                    icon: const Icon(Icons.logout_rounded, color: AppColors.error),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.only(left: 4.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Hello, ${widget.user.username.replaceAll('_', ' ')}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _profile?.category ?? 'Worker workspace',
                  style: const TextStyle(
                    color: Color(0xFF6E7489),
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileCard() {
    final profile = _profile;
    if (profile == null) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.fromLTRB(20, 8, 20, 18),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2E6F2), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.025),
            blurRadius: 16,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: AppColors.lightPrimary.withValues(alpha: 0.08),
            child: const Icon(
              Icons.engineering_rounded,
              color: AppColors.lightPrimary,
              size: 28,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Rs. ${profile.price.toStringAsFixed(0)}/hr',
                  style: const TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${profile.experienceYears} years exp. • ${profile.rating.toStringAsFixed(1)} rating',
                  style: const TextStyle(
                    color: Color(0xFF6E7489),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                profile.isOnline ? 'Online' : 'Offline',
                style: TextStyle(
                  color: profile.isOnline
                      ? AppColors.success
                      : const Color(0xFFA2A7B8),
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
              Switch(
                value: profile.isOnline,
                activeThumbColor: AppColors.success,
                inactiveThumbColor: const Color(0xFFA2A7B8),
                onChanged: _isUpdatingAvailability ? null : _setAvailability,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMetrics() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: GridView.count(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 1.45,
        children: [
          _buildMetricCard(
            'Pending',
            '${_metrics.pendingRequests}',
            Icons.inbox_outlined,
            AppColors.warning,
          ),
          _buildMetricCard(
            'Active Jobs',
            '${_metrics.activeJobs}',
            Icons.work_outline_rounded,
            AppColors.lightPrimary,
          ),
          _buildMetricCard(
            'Completed',
            '${_metrics.completedJobs}',
            Icons.verified_outlined,
            AppColors.success,
          ),
          _buildMetricCard(
            'Earnings',
            'Rs. ${_metrics.totalEarnings.toStringAsFixed(0)}',
            Icons.payments_outlined,
            const Color(0xFF26A69A),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(
    String title,
    String value,
    IconData icon,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2E6F2), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          CircleAvatar(
            radius: 18,
            backgroundColor: color.withValues(alpha: 0.1),
            child: Icon(icon, color: color, size: 20),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Color(0xFF1E212D),
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                title,
                style: const TextStyle(
                  color: Color(0xFF6E7489),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFilters() {
    final filters = <String, String>{
      'all': 'All',
      'requested': 'Requests',
      'accepted': 'Accepted',
      'on_the_way': 'On Way',
      'in_progress': 'Working',
      'completed': 'Done',
    };

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Bookings',
            style: TextStyle(
              color: Color(0xFF1E212D),
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: filters.entries.map((entry) {
                final selected = _selectedFilter == entry.key;
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
                      setState(() {
                        _selectedFilter = entry.key;
                      });
                      await _loadDashboard();
                    },
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBookingCard(BookingModel booking) {
    final isUpdating = _updatingBookingId == booking.id;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2E6F2), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: AppColors.lightPrimary.withValues(alpha: 0.08),
                child: Text(
                  booking.customer.username.substring(0, 1).toUpperCase(),
                  style: const TextStyle(
                    color: AppColors.lightPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      booking.customer.username.replaceAll('_', ' '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF1E212D),
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      booking.serviceCategory,
                      style: const TextStyle(
                        color: Color(0xFF6E7489),
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              _buildStatusPill(booking),
            ],
          ),
          const SizedBox(height: 14),
          _buildBookingInfo(
            Icons.schedule_rounded,
            _formatDateTime(booking.scheduledAt),
          ),
          const SizedBox(height: 8),
          _buildBookingInfo(Icons.location_on_outlined, booking.address),
          if (booking.description.isNotEmpty) ...[
            const SizedBox(height: 8),
            _buildBookingInfo(Icons.notes_rounded, booking.description),
          ],
          const SizedBox(height: 14),
          if (booking.conversationId != null)
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
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
                label: const Text('Chat with customer'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.lightPrimary,
                ),
              ),
            ),
          if (booking.conversationId != null) const SizedBox(height: 10),
          Row(
            children: [
              Text(
                'Rs. ${booking.totalAmount.toStringAsFixed(0)}',
                style: const TextStyle(
                  color: AppColors.lightPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              if (isUpdating)
                const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              else
                ..._buildBookingActions(booking),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBookingInfo(IconData icon, String text) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: const Color(0xFFA2A7B8), size: 17),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              color: Color(0xFF6E7489),
              fontSize: 13,
              height: 1.35,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStatusPill(BookingModel booking) {
    final color = switch (booking.status) {
      'requested' => AppColors.warning,
      'accepted' => AppColors.lightPrimary,
      'on_the_way' => const Color(0xFF7E57C2),
      'in_progress' => const Color(0xFF26A69A),
      'completed' => AppColors.success,
      'declined' || 'cancelled' => AppColors.error,
      _ => const Color(0xFF6E7489),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
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

  List<Widget> _buildBookingActions(BookingModel booking) {
    switch (booking.status) {
      case 'requested':
        return [
          _smallButton(
            'Decline',
            AppColors.error,
            () => _updateBookingStatus(booking, 'declined'),
            outlined: true,
          ),
          const SizedBox(width: 8),
          _smallButton(
            'Accept',
            AppColors.success,
            () => _updateBookingStatus(booking, 'accepted'),
          ),
        ];
      case 'accepted':
        return [
          _smallButton(
            'On Way',
            AppColors.lightPrimary,
            () => _updateBookingStatus(booking, 'on_the_way'),
          ),
        ];
      case 'on_the_way':
        return [
          _smallButton(
            'Start',
            const Color(0xFF26A69A),
            () => _updateBookingStatus(booking, 'in_progress'),
          ),
        ];
      case 'in_progress':
        return [
          _smallButton(
            'Complete',
            AppColors.success,
            () => _updateBookingStatus(booking, 'completed'),
          ),
        ];
      default:
        return [];
    }
  }

  Widget _smallButton(
    String label,
    Color color,
    VoidCallback onPressed, {
    bool outlined = false,
  }) {
    if (outlined) {
      return OutlinedButton(
        style: OutlinedButton.styleFrom(
          foregroundColor: color,
          side: BorderSide(color: color.withValues(alpha: 0.5)),
          visualDensity: VisualDensity.compact,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
        onPressed: onPressed,
        child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
      );
    }

    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        elevation: 0,
        visualDensity: VisualDensity.compact,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      onPressed: onPressed,
      child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildEmptyState() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 40),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 36),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFE2E6F2)),
        ),
        child: const Column(
          children: [
            Icon(
              Icons.event_available_outlined,
              color: AppColors.lightPrimary,
              size: 44,
            ),
            SizedBox(height: 14),
            Text(
              'No bookings here yet',
              style: TextStyle(
                color: Color(0xFF1E212D),
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Keep your availability online so nearby customers can send requests.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFF6E7489), height: 1.4),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 40),
      child: Text(
        message,
        style: const TextStyle(
          color: AppColors.error,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    final date =
        '${dateTime.day.toString().padLeft(2, '0')}/'
        '${dateTime.month.toString().padLeft(2, '0')}/'
        '${dateTime.year}';
    final hour = dateTime.hour > 12
        ? dateTime.hour - 12
        : dateTime.hour == 0
        ? 12
        : dateTime.hour;
    final minute = dateTime.minute.toString().padLeft(2, '0');
    final period = dateTime.hour >= 12 ? 'PM' : 'AM';
    return '$date • $hour:$minute $period';
  }
}
