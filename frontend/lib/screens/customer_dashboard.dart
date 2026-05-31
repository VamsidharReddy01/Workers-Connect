import 'package:flutter/material.dart';
import '../models/category_model.dart';
import '../models/user_model.dart';
import '../models/worker_profile_model.dart';
import '../services/worker_service.dart';
import '../utils/constants.dart';
import 'worker_detail_screen.dart';

class CustomerDashboard extends StatefulWidget {
  final UserModel user;
  final VoidCallback? onBookingCreated;

  const CustomerDashboard({
    super.key,
    required this.user,
    this.onBookingCreated,
  });

  @override
  State<CustomerDashboard> createState() => _CustomerDashboardState();
}

class _CustomerDashboardState extends State<CustomerDashboard> {
  final TextEditingController _searchController = TextEditingController();
  final WorkerService _workerService = WorkerService();

  List<CategoryModel> _categories = [];
  List<WorkerProfileModel> _workers = [];
  String? _selectedCategory;
  bool _isLoadingCategories = true;
  bool _isLoadingWorkers = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoadingCategories = true;
      _isLoadingWorkers = true;
    });

    try {
      final categories = await _workerService.getCategories();
      final workers = await _workerService.getNearbyWorkers();

      setState(() {
        _categories = categories;
        _workers = workers;
        _isLoadingCategories = false;
        _isLoadingWorkers = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingCategories = false;
        _isLoadingWorkers = false;
      });
    }
  }

  Future<void> _filterWorkers({String? category, String? search}) async {
    setState(() {
      _isLoadingWorkers = true;
    });

    try {
      final workers = await _workerService.getNearbyWorkers(
        category: category,
        search: search,
      );
      setState(() {
        _workers = workers;
        _isLoadingWorkers = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingWorkers = false;
      });
    }
  }

  Future<void> _openWorkerDetail(WorkerProfileModel worker) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => WorkerDetailScreen(
          worker: worker,
          customer: widget.user,
          onBookingCreated: widget.onBookingCreated,
        ),
      ),
    );
    if (!mounted) return;
    await _filterWorkers(
      category: _selectedCategory,
      search: _searchController.text.trim(),
    );
  }

  String get _workersSectionTitle {
    if (_selectedCategory != null && _selectedCategory!.isNotEmpty) {
      return '$_selectedCategory Workers';
    }
    return 'Registered Workers';
  }

  IconData _getCategoryIcon(String categoryName) {
    switch (categoryName.toLowerCase()) {
      case 'electrician':
        return Icons.bolt_rounded;
      case 'plumber':
        return Icons.plumbing_rounded;
      case 'carpenter':
        return Icons.handyman_rounded;
      case 'painter':
        return Icons.format_paint_rounded;
      case 'house cleaner':
      case 'cleaner':
      case 'cleaning':
        return Icons.cleaning_services_rounded;
      case 'ac repair':
      case 'ac':
        return Icons.ac_unit_rounded;
      default:
        return Icons.work_outline_rounded;
    }
  }

  Color _getCategoryColor(String categoryName) {
    switch (categoryName.toLowerCase()) {
      case 'electrician':
        return const Color(0xFFFFB300); // Yellow/Amber
      case 'plumber':
        return const Color(0xFF1E88E5); // Blue
      case 'carpenter':
        return const Color(0xFF8D6E63); // Brown
      case 'painter':
        return const Color(0xFFEC407A); // Pink
      case 'house cleaner':
      case 'cleaner':
      case 'cleaning':
        return const Color(0xFF26A69A); // Green/Teal
      case 'ac repair':
      case 'ac':
        return const Color(0xFF29B6F6); // Light Blue
      default:
        return const Color(0xFF78909C); // Blue Grey
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadData,
          color: AppColors.lightPrimary,
          backgroundColor: Colors.white,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(
              parent: BouncingScrollPhysics(),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 16),

                // Custom Header Matching Mockup
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    IconButton(
                      icon: const Icon(
                        Icons.menu_rounded,
                        color: Color(0xFF1E212D),
                        size: 28,
                      ),
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Side drawer menu option clicked'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      },
                    ),
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
                    Stack(
                      children: [
                        IconButton(
                          icon: const Icon(
                            Icons.notifications_none_rounded,
                            color: Color(0xFF1E212D),
                            size: 28,
                          ),
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Notifications screen clicked'),
                                behavior: SnackBarBehavior.floating,
                              ),
                            );
                          },
                        ),
                        Positioned(
                          right: 12,
                          top: 12,
                          child: Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: AppColors.error,
                              shape: BoxShape.circle,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),

                const SizedBox(height: 16),

                // User Greeting Header
                Text(
                  'Hi, ${widget.user.username} 👋',
                  style: const TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'What service do you need today?',
                  style: TextStyle(
                    color: Color(0xFF6E7489),
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                  ),
                ),

                const SizedBox(height: 24),

                // Search Bar Matching Mockup
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: const Color(0xFFE2E6F2),
                      width: 1.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.015),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: TextField(
                    controller: _searchController,
                    style: const TextStyle(
                      color: Color(0xFF1E212D),
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                    cursorColor: AppColors.lightPrimary,
                    decoration: InputDecoration(
                      hintText: 'Search for services or workers...',
                      hintStyle: const TextStyle(
                        color: Color(0xFFA2A7B8),
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                      prefixIcon: const Icon(
                        Icons.search_rounded,
                        color: Color(0xFFA2A7B8),
                        size: 22,
                      ),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    onSubmitted: (query) {
                      _filterWorkers(
                        category: _selectedCategory,
                        search: query.trim(),
                      );
                    },
                  ),
                ),

                const SizedBox(height: 28),

                // Popular Categories Section Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Popular Categories',
                      style: TextStyle(
                        color: Color(0xFF1E212D),
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _selectedCategory = null;
                          _searchController.clear();
                        });
                        _loadData();
                      },
                      child: const Text(
                        'View all',
                        style: TextStyle(
                          color: AppColors.lightPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Popular Categories Grid (3x2 GridView inline)
                _isLoadingCategories
                    ? const Center(
                        child: Padding(
                          padding: EdgeInsets.symmetric(vertical: 24.0),
                          child: CircularProgressIndicator(strokeWidth: 2.5),
                        ),
                      )
                    : _categories.isEmpty
                    ? Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFE2E6F2)),
                        ),
                        child: const Center(
                          child: Text(
                            'No worker services configured yet.',
                            style: TextStyle(
                              color: Color(0xFF6E7489),
                              fontSize: 13,
                            ),
                          ),
                        ),
                      )
                    : GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _categories.length > 6
                            ? 6
                            : _categories.length,
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 3,
                              crossAxisSpacing: 12,
                              mainAxisSpacing: 12,
                              childAspectRatio: 0.95,
                            ),
                        itemBuilder: (context, index) {
                          final cat = _categories[index];
                          final isSelected = _selectedCategory == cat.name;
                          final themeColor = _getCategoryColor(cat.name);

                          return GestureDetector(
                            onTap: () {
                              setState(() {
                                if (_selectedCategory == cat.name) {
                                  _selectedCategory = null;
                                } else {
                                  _selectedCategory = cat.name;
                                }
                              });
                              _filterWorkers(
                                category: _selectedCategory,
                                search: _searchController.text.trim(),
                              );
                            },
                            child: Container(
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? themeColor.withValues(alpha: 0.08)
                                    : Colors.white,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: isSelected
                                      ? themeColor.withValues(alpha: 0.4)
                                      : const Color(0xFFE2E6F2),
                                  width: 1.5,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withValues(alpha: 0.01),
                                    blurRadius: 8,
                                    offset: const Offset(0, 3),
                                  ),
                                ],
                              ),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: themeColor.withValues(alpha: 0.12),
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      _getCategoryIcon(cat.name),
                                      color: themeColor,
                                      size: 24,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    cat.name,
                                    textAlign: TextAlign.center,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(
                                      color: isSelected
                                          ? themeColor
                                          : const Color(0xFF1E212D),
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    '${cat.workerCount} ${cat.workerCount == 1 ? 'worker' : 'workers'}',
                                    textAlign: TextAlign.center,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: Color(0xFF6E7489),
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),

                const SizedBox(height: 28),

                // Nearby Workers Section Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _workersSectionTitle,
                            style: const TextStyle(
                              color: Color(0xFF1E212D),
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          if (_selectedCategory != null)
                            Text(
                              '${_workers.length} registered in this category',
                              style: const TextStyle(
                                color: Color(0xFF6E7489),
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                        ],
                      ),
                    ),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _selectedCategory = null;
                          _searchController.clear();
                        });
                        _loadData();
                      },
                      child: const Text(
                        'View all',
                        style: TextStyle(
                          color: AppColors.lightPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Nearby Workers List View Matching Mockup
                _isLoadingWorkers
                    ? const Center(
                        child: Padding(
                          padding: EdgeInsets.symmetric(vertical: 32.0),
                          child: CircularProgressIndicator(strokeWidth: 2.5),
                        ),
                      )
                    : _workers.isEmpty
                    ? Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                          vertical: 40,
                          horizontal: 20,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: const Color(0xFFE2E6F2)),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.people_outline_rounded,
                              color: const Color(0xFFA2A7B8),
                              size: 48,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              _selectedCategory != null
                                  ? 'No workers registered in this category yet.'
                                  : 'No workers available matching your criteria.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: Color(0xFF6E7489),
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _workers.length,
                        itemBuilder: (context, index) {
                          final worker = _workers[index];
                          final workerLocation =
                              worker.user.location?.trim().isNotEmpty == true
                              ? worker.user.location!.trim()
                              : 'Location not set';
                          final displayName = worker.user.username.replaceAll(
                            '_',
                            ' ',
                          );
                          final avatarText = displayName.trim().isEmpty
                              ? 'W'
                              : displayName
                                    .trim()
                                    .split(RegExp(r'\s+'))
                                    .where((part) => part.isNotEmpty)
                                    .take(2)
                                    .map((part) => part[0])
                                    .join()
                                    .toUpperCase();

                          return Container(
                            margin: const EdgeInsets.only(bottom: 16),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: const Color(0xFFE2E6F2),
                                width: 1.5,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.01),
                                  blurRadius: 10,
                                  offset: const Offset(0, 4),
                                ),
                              ],
                            ),
                            child: InkWell(
                              borderRadius: BorderRadius.circular(20),
                              onTap: () => _openWorkerDetail(worker),
                              child: Row(
                                children: [
                                  // Worker avatar / portfolio preview
                                  ClipRRect(
                                    borderRadius: BorderRadius.circular(18),
                                    child: Container(
                                      width: 72,
                                      height: 72,
                                      decoration: BoxDecoration(
                                        color: AppColors.lightPrimary
                                            .withValues(alpha: 0.05),
                                        border: Border.all(
                                          color: AppColors.lightPrimary
                                              .withValues(alpha: 0.15),
                                        ),
                                        borderRadius: BorderRadius.circular(18),
                                      ),
                                      child: worker.coverImageUrl != null
                                          ? Image.network(
                                              ApiConstants.resolveMediaUrl(
                                                worker.coverImageUrl,
                                              ),
                                              fit: BoxFit.cover,
                                              errorBuilder: (_, __, ___) =>
                                                  Center(
                                                child: Text(
                                                  avatarText,
                                                  style: const TextStyle(
                                                    color: AppColors.lightPrimary,
                                                    fontSize: 18,
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                              ),
                                            )
                                          : Center(
                                              child: Text(
                                                avatarText,
                                                style: const TextStyle(
                                                  color: AppColors.lightPrimary,
                                                  fontSize: 18,
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                            ),
                                    ),
                                  ),
                                  const SizedBox(width: 14),

                                  // Worker details column
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          displayName,
                                          style: const TextStyle(
                                            color: Color(0xFF1E212D),
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                        const SizedBox(height: 3),
                                        Text(
                                          worker.category,
                                          style: const TextStyle(
                                            color: Color(0xFF6E7489),
                                            fontSize: 13,
                                            fontWeight: FontWeight.w500,
                                          ),
                                        ),
                                        const SizedBox(height: 6),

                                        // Sub-row with stars & reviews
                                        Row(
                                          children: [
                                            const Icon(
                                              Icons.star_rounded,
                                              color: Color(0xFFFFA726),
                                              size: 16,
                                            ),
                                            const SizedBox(width: 4),
                                            Text(
                                              '${worker.rating}',
                                              style: const TextStyle(
                                                color: Color(0xFF1E212D),
                                                fontSize: 12,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                            const SizedBox(width: 3),
                                            Text(
                                              '(${worker.totalReviews})',
                                              style: const TextStyle(
                                                color: Color(0xFFA2A7B8),
                                                fontSize: 12,
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 5),
                                        Wrap(
                                          spacing: 8,
                                          runSpacing: 4,
                                          children: [
                                            Row(
                                              mainAxisSize: MainAxisSize.min,
                                              children: [
                                                const Icon(
                                                  Icons.place_outlined,
                                                  color: Color(0xFFA2A7B8),
                                                  size: 14,
                                                ),
                                                const SizedBox(width: 3),
                                                ConstrainedBox(
                                                  constraints:
                                                      const BoxConstraints(
                                                        maxWidth: 130,
                                                      ),
                                                  child: Text(
                                                    workerLocation,
                                                    maxLines: 1,
                                                    overflow:
                                                        TextOverflow.ellipsis,
                                                    style: const TextStyle(
                                                      color: Color(0xFFA2A7B8),
                                                      fontSize: 12,
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                            Container(
                                              padding:
                                                  const EdgeInsets.symmetric(
                                                    horizontal: 8,
                                                    vertical: 3,
                                                  ),
                                              decoration: BoxDecoration(
                                                color:
                                                    (worker.isOnline
                                                            ? AppColors.success
                                                            : const Color(
                                                                0xFFA2A7B8,
                                                              ))
                                                        .withValues(
                                                          alpha: 0.12,
                                                        ),
                                                borderRadius:
                                                    BorderRadius.circular(999),
                                              ),
                                              child: Text(
                                                worker.isOnline
                                                    ? 'Available'
                                                    : 'Offline',
                                                style: TextStyle(
                                                  color: worker.isOnline
                                                      ? AppColors.success
                                                      : const Color(0xFF6E7489),
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),

                                  // Price and availability column (right side)
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text(
                                        '₹${worker.price.toStringAsFixed(0)}/hr',
                                        style: const TextStyle(
                                          color: AppColors.lightPrimary,
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 6),
                                      Text(
                                        worker.isOnline
                                            ? 'View profile'
                                            : 'View profile',
                                        style: TextStyle(
                                          color: worker.isOnline
                                              ? const Color(0xFF6E7489)
                                              : const Color(0xFFA2A7B8),
                                          fontSize: 12,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),

                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
