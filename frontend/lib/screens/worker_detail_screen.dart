import 'package:flutter/material.dart';

import '../models/user_model.dart';
import '../models/worker_profile_model.dart';
import '../services/worker_service.dart';
import '../utils/constants.dart';
import 'chat_screen.dart';

class WorkerDetailScreen extends StatefulWidget {
  final WorkerProfileModel worker;
  final UserModel customer;
  final VoidCallback? onBookingCreated;

  const WorkerDetailScreen({
    super.key,
    required this.worker,
    required this.customer,
    this.onBookingCreated,
  });

  @override
  State<WorkerDetailScreen> createState() => _WorkerDetailScreenState();
}

class _WorkerDetailScreenState extends State<WorkerDetailScreen> {
  final WorkerService _workerService = WorkerService();
  WorkerProfileModel? _worker;
  bool _isLoading = true;
  bool _isBooking = false;

  @override
  void initState() {
    super.initState();
    _loadWorker();
  }

  Future<void> _loadWorker() async {
    setState(() => _isLoading = true);
    final detail = await _workerService.getWorkerDetail(widget.worker.id);
    if (!mounted) return;
    setState(() {
      _worker = detail ?? widget.worker;
      _isLoading = false;
    });
  }

  Future<void> _bookWorker() async {
    final worker = _worker ?? widget.worker;
    if (!worker.isOnline || _isBooking) return;

    setState(() => _isBooking = true);
    final booking = await _workerService.createBooking(
      workerId: worker.id,
      serviceCategory: worker.category,
      address: widget.customer.location ?? 'Customer address not specified',
      scheduledAt: DateTime.now().add(const Duration(days: 1)),
      totalAmount: worker.price,
      description: 'Booking request from ${widget.customer.username}.',
    );
    if (!mounted) return;

    setState(() => _isBooking = false);
    final messenger = ScaffoldMessenger.of(context);

    if (booking == null) {
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            _workerService.lastErrorMessage ??
                'Could not create booking. Please try again.',
          ),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    messenger.showSnackBar(
      SnackBar(
        content: Text(
          'Booking request sent to ${_displayName(worker.user.username)}.',
        ),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );

    widget.onBookingCreated?.call();

    if (booking.conversationId != null && mounted) {
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ChatScreen(
            currentUser: widget.customer,
            conversationId: booking.conversationId!,
            title: _displayName(worker.user.username),
            subtitle: worker.category,
          ),
        ),
      );
    }
  }

  String _displayName(String username) => username.replaceAll('_', ' ');

  String _avatarText(String username) {
    final displayName = _displayName(username);
    if (displayName.trim().isEmpty) return 'W';
    return displayName
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .take(2)
        .map((part) => part[0])
        .join()
        .toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final worker = _worker ?? widget.worker;
    final location = worker.user.location?.trim().isNotEmpty == true
        ? worker.user.location!.trim()
        : 'Location not set';
    final phone = worker.user.phoneNumber?.trim();

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1E212D),
        elevation: 0,
        surfaceTintColor: Colors.white,
        title: const Text(
          'Worker Profile',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(strokeWidth: 2.5))
          : RefreshIndicator(
              onRefresh: _loadWorker,
              color: AppColors.lightPrimary,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _ProfileHeader(
                      worker: worker,
                      displayName: _displayName(worker.user.username),
                      avatarText: _avatarText(worker.user.username),
                    ),
                    const SizedBox(height: 20),
                    _InfoCard(
                      children: [
                        _InfoRow(
                          icon: Icons.place_outlined,
                          label: 'Location',
                          value: location,
                        ),
                        if (phone != null && phone.isNotEmpty)
                          _InfoRow(
                            icon: Icons.phone_outlined,
                            label: 'Phone',
                            value: phone,
                          ),
                        _InfoRow(
                          icon: Icons.history_edu_outlined,
                          label: 'Experience',
                          value: '${worker.experienceYears} years',
                        ),
                        _InfoRow(
                          icon: Icons.payments_outlined,
                          label: 'Hourly rate',
                          value: '₹${worker.price.toStringAsFixed(0)}/hr',
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    _SectionTitle('About'),
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFE2E6F2)),
                      ),
                      child: Text(
                        worker.bio.trim().isNotEmpty
                            ? worker.bio.trim()
                            : 'This worker has not added a bio yet.',
                        style: TextStyle(
                          color: worker.bio.trim().isNotEmpty
                              ? const Color(0xFF1E212D)
                              : const Color(0xFF6E7489),
                          fontSize: 14,
                          height: 1.5,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    _SectionTitle('Work Portfolio'),
                    const SizedBox(height: 8),
                    if (worker.workImages.isEmpty)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFE2E6F2)),
                        ),
                        child: const Column(
                          children: [
                            Icon(
                              Icons.photo_library_outlined,
                              color: Color(0xFFA2A7B8),
                              size: 40,
                            ),
                            SizedBox(height: 8),
                            Text(
                              'No portfolio photos uploaded yet.',
                              style: TextStyle(color: Color(0xFF6E7489)),
                            ),
                          ],
                        ),
                      )
                    else
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: worker.workImages.length,
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 2,
                              crossAxisSpacing: 12,
                              mainAxisSpacing: 12,
                              childAspectRatio: 1.1,
                            ),
                        itemBuilder: (context, index) {
                          final image = worker.workImages[index];
                          return ClipRRect(
                            borderRadius: BorderRadius.circular(16),
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                Image.network(
                                  ApiConstants.resolveMediaUrl(image.imageUrl),
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => Container(
                                    color: const Color(0xFFF1F3F8),
                                    child: const Icon(
                                      Icons.broken_image_outlined,
                                    ),
                                  ),
                                ),
                                if (image.caption != null &&
                                    image.caption!.trim().isNotEmpty)
                                  Positioned(
                                    left: 0,
                                    right: 0,
                                    bottom: 0,
                                    child: Container(
                                      padding: const EdgeInsets.all(8),
                                      color: Colors.black.withValues(
                                        alpha: 0.45,
                                      ),
                                      child: Text(
                                        image.caption!,
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 12,
                                        ),
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          );
                        },
                      ),
                  ],
                ),
              ),
            ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
          child: SizedBox(
            height: 54,
            child: ElevatedButton(
              onPressed: worker.isOnline && !_isBooking ? _bookWorker : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.lightPrimary,
                disabledBackgroundColor: const Color(0xFFE2E6F2),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                elevation: 0,
              ),
              child: _isBooking
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : Text(
                      worker.isOnline
                          ? 'Book ${worker.category}'
                          : 'Currently unavailable',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  final WorkerProfileModel worker;
  final String displayName;
  final String avatarText;

  const _ProfileHeader({
    required this.worker,
    required this.displayName,
    required this.avatarText,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE2E6F2)),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 38,
            backgroundColor: AppColors.lightPrimary.withValues(alpha: 0.08),
            backgroundImage: worker.coverImageUrl != null
                ? NetworkImage(
                    ApiConstants.resolveMediaUrl(worker.coverImageUrl),
                  )
                : null,
            child: worker.coverImageUrl == null
                ? Text(
                    avatarText,
                    style: const TextStyle(
                      color: AppColors.lightPrimary,
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                    ),
                  )
                : null,
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  displayName,
                  style: const TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  worker.category,
                  style: const TextStyle(
                    color: Color(0xFF6E7489),
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(
                      Icons.star_rounded,
                      color: Color(0xFFFFA726),
                      size: 18,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${worker.rating}',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1E212D),
                      ),
                    ),
                    Text(
                      ' (${worker.totalReviews} reviews)',
                      style: const TextStyle(
                        color: Color(0xFF6E7489),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color:
                        (worker.isOnline
                                ? AppColors.success
                                : const Color(0xFFA2A7B8))
                            .withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    worker.isOnline ? 'Available now' : 'Offline',
                    style: TextStyle(
                      color: worker.isOnline
                          ? AppColors.success
                          : const Color(0xFF6E7489),
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;

  const _SectionTitle(this.title);

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        color: Color(0xFF1E212D),
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final List<Widget> children;

  const _InfoCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E6F2)),
      ),
      child: Column(children: children),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFFA2A7B8)),
          const SizedBox(width: 10),
          SizedBox(
            width: 92,
            child: Text(
              label,
              style: const TextStyle(
                color: Color(0xFF6E7489),
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Color(0xFF1E212D),
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
