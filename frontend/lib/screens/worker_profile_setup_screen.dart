import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/user_model.dart';
import '../models/worker_profile_model.dart';
import '../models/worker_work_image_model.dart';
import '../services/worker_service.dart';
import '../theme/light_form_theme.dart';
import '../utils/constants.dart';
import '../widgets/work_portfolio_picker.dart';
import 'worker_dashboard.dart';

class WorkerProfileSetupScreen extends StatefulWidget {
  final UserModel user;
  final WorkerProfileModel? existingProfile;
  final bool isEditing;

  const WorkerProfileSetupScreen({
    super.key,
    required this.user,
    this.existingProfile,
    this.isEditing = false,
  });

  @override
  State<WorkerProfileSetupScreen> createState() =>
      _WorkerProfileSetupScreenState();
}

class _WorkerProfileSetupScreenState extends State<WorkerProfileSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _priceController = TextEditingController();
  final _experienceController = TextEditingController(text: '1');
  final _bioController = TextEditingController();
  final ImagePicker _imagePicker = ImagePicker();

  static const List<String> _fallbackCategories = [
    'Electrician',
    'Plumber',
    'Carpenter',
    'Painter',
    'House Cleaner',
    'AC Repair',
  ];

  List<String> _predefinedCategories = List.from(_fallbackCategories);
  List<WorkerWorkImageModel> _existingImages = [];
  List<PortfolioLocalImage> _pendingImages = [];
  final Set<int> _removedExistingIds = {};
  String? _selectedCategory;
  final _customCategoryController = TextEditingController();
  bool _isCustomCategory = false;
  bool _isLoading = false;
  bool _loadingCategories = true;
  String? _errorMsg;

  bool get _isEditing => widget.isEditing || widget.existingProfile != null;

  @override
  void initState() {
    super.initState();
    _loadCategories();
    _prefillExistingProfile();
  }

  void _prefillExistingProfile() {
    final profile = widget.existingProfile;
    if (profile == null) return;

    _priceController.text = profile.price.toStringAsFixed(
      profile.price % 1 == 0 ? 0 : 2,
    );
    _experienceController.text = profile.experienceYears.toString();
    _bioController.text = profile.bio;
    _existingImages = List.from(profile.workImages);

    if (_predefinedCategories.contains(profile.category)) {
      _selectedCategory = profile.category;
      _isCustomCategory = false;
    } else {
      _isCustomCategory = true;
      _customCategoryController.text = profile.category;
    }
  }

  Future<void> _loadCategories() async {
    final workerService = WorkerService();
    final fromApi = await workerService.getJobCategoryOptions();
    if (!mounted) return;
    setState(() {
      if (fromApi.isNotEmpty) {
        _predefinedCategories = fromApi;
        final profile = widget.existingProfile;
        if (profile != null && fromApi.contains(profile.category)) {
          _selectedCategory = profile.category;
          _isCustomCategory = false;
        }
      }
      _loadingCategories = false;
    });
  }

  Future<void> _pickPortfolioImages() async {
    final totalCount =
        _existingImages.where((img) => !_removedExistingIds.contains(img.id)).length +
        _pendingImages.length;
    if (totalCount >= 8) {
      setState(() {
        _errorMsg = 'You can upload up to 8 portfolio photos.';
      });
      return;
    }

    final picked = await _imagePicker.pickMultiImage(imageQuality: 80);
    if (picked.isEmpty || !mounted) return;

    final remainingSlots = 8 - totalCount;
    final selected = picked.take(remainingSlots).toList();
    final localImages = <PortfolioLocalImage>[];
    for (final file in selected) {
      final local = await PortfolioLocalImage.fromXFile(file);
      if (local != null) localImages.add(local);
    }

    setState(() {
      _pendingImages.addAll(localImages);
      _errorMsg = null;
    });
  }

  @override
  void dispose() {
    _priceController.dispose();
    _experienceController.dispose();
    _customCategoryController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    if (widget.user.role != 'worker') {
      setState(() {
        _errorMsg =
            'This account is registered as ${widget.user.roleDisplay}. Please sign up or log in as a worker.';
      });
      return;
    }

    final category = _isCustomCategory
        ? _customCategoryController.text.trim()
        : _selectedCategory;

    if (category == null || category.isEmpty) {
      setState(() {
        _errorMsg = 'Please select or type your specialty category.';
      });
      return;
    }

    final price = double.tryParse(_priceController.text) ?? 0.0;
    final experience = int.tryParse(_experienceController.text) ?? 1;

    setState(() {
      _isLoading = true;
      _errorMsg = null;
    });

    final workerService = WorkerService();
    final profile = _isEditing
        ? await workerService.updateProfile(
            category: category,
            price: price,
            experienceYears: experience,
            bio: _bioController.text,
          )
        : await workerService.saveProfile(
            category: category,
            price: price,
            experienceYears: experience,
            bio: _bioController.text,
          );

    if (profile == null) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _errorMsg =
            workerService.lastErrorMessage ??
            'Failed to save job profile. Please try again.';
      });
      return;
    }

    for (final imageId in _removedExistingIds) {
      await workerService.deleteWorkImage(imageId);
    }

    if (_pendingImages.isNotEmpty) {
      final uploaded = await workerService.uploadWorkImages(
        _pendingImages
            .map(
              (img) => PortfolioUploadFile(
                filename: img.filename,
                bytes: img.bytes,
              ),
            )
            .toList(),
      );
      if (uploaded.isEmpty && workerService.lastErrorMessage != null) {
        if (!mounted) return;
        setState(() {
          _isLoading = false;
          _errorMsg = workerService.lastErrorMessage;
        });
        return;
      }
    }

    if (!mounted) return;

    setState(() => _isLoading = false);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _isEditing
              ? 'Job profile updated successfully.'
              : 'Job profile saved successfully! Welcome to your dashboard.',
        ),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );

    if (_isEditing) {
      Navigator.of(context).pop(true);
    } else {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => WorkerDashboard(user: widget.user)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: LightFormTheme.of(context),
      child: Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1E212D),
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.white,
        title: Text(
          _isEditing ? 'Edit Job Profile' : 'Create Job Profile',
          style: const TextStyle(
            color: Color(0xFF1E212D),
            fontWeight: FontWeight.bold,
          ),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFFE2E6F2), height: 1),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Set Up Your Services',
                  style: TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  _isEditing
                      ? 'Update your specialty, pricing, bio, and portfolio photos.'
                      : 'Fill in your work specialty and pricing so customers can find and book your services!',
                  style: const TextStyle(
                    color: Color(0xFF6E7489),
                    fontSize: 14,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 28),

                if (_errorMsg != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.error.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: AppColors.error.withValues(alpha: 0.3),
                      ),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.error_outline,
                          color: AppColors.error,
                          size: 20,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            _errorMsg!,
                            style: const TextStyle(
                              color: AppColors.error,
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // Specialty Category dropdown or custom text field
                const Text(
                  'Your Work Specialty / Category',
                  style: TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),

                if (!_isCustomCategory) ...[
                  if (_loadingCategories)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Center(
                        child: SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                    )
                  else
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: const Color(0xFFE2E6F2),
                          width: 1.5,
                        ),
                      ),
                      child: DropdownButtonFormField<String>(
                        initialValue: _selectedCategory,
                        dropdownColor: Colors.white,
                        iconEnabledColor: const Color(0xFF6E7489),
                        iconDisabledColor: const Color(0xFFA2A7B8),
                        borderRadius: BorderRadius.circular(12),
                        menuMaxHeight: 320,
                        hint: const Text(
                          'Select Specialty Category',
                          style: TextStyle(
                            color: Color(0xFFA2A7B8),
                            fontSize: 14,
                          ),
                        ),
                        style: const TextStyle(
                          color: Color(0xFF1E212D),
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                        ),
                        decoration: const InputDecoration(
                          border: InputBorder.none,
                        ),
                        items: _predefinedCategories.map((cat) {
                          return DropdownMenuItem<String>(
                            value: cat,
                            child: Text(
                              cat,
                              style: const TextStyle(
                                color: Color(0xFF1E212D),
                                fontSize: 15,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          );
                        }).toList(),
                        selectedItemBuilder: (context) {
                          return _predefinedCategories.map((cat) {
                            return Align(
                              alignment: Alignment.centerLeft,
                              child: Text(
                                cat,
                                style: const TextStyle(
                                  color: Color(0xFF1E212D),
                                  fontSize: 15,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            );
                          }).toList();
                        },
                        onChanged: (val) {
                          setState(() {
                            _selectedCategory = val;
                          });
                        },
                      ),
                    ),
                  const SizedBox(height: 12),
                  TextButton.icon(
                    onPressed: () {
                      setState(() {
                        _isCustomCategory = true;
                        _selectedCategory = null;
                      });
                    },
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Add Custom Category Specialty'),
                    style: TextButton.styleFrom(
                      foregroundColor: AppColors.lightPrimary,
                    ),
                  ),
                ] else ...[
                  _buildTextField(
                    controller: _customCategoryController,
                    hintText: 'e.g. Painter, House Cleaner, Carpenter',
                    prefixIcon: Icons.handyman_outlined,
                    validator: (val) {
                      if (val == null || val.trim().isEmpty) {
                        return 'Please specify your specialty category.';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 12),
                  TextButton.icon(
                    onPressed: () {
                      setState(() {
                        _isCustomCategory = false;
                        _customCategoryController.clear();
                      });
                    },
                    icon: const Icon(Icons.list, size: 18),
                    label: const Text('Select from Predefined List'),
                    style: TextButton.styleFrom(
                      foregroundColor: AppColors.lightPrimary,
                    ),
                  ),
                ],

                const SizedBox(height: 24),

                const Text(
                  'About Your Work',
                  style: TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),
                _buildTextField(
                  controller: _bioController,
                  hintText: 'Describe your skills, specialties, and experience...',
                  prefixIcon: Icons.description_outlined,
                  maxLines: 4,
                ),

                const SizedBox(height: 24),

                WorkPortfolioPicker(
                  existingImages: _existingImages,
                  pendingImages: _pendingImages,
                  removedExistingIds: _removedExistingIds,
                  onPickImages: _pickPortfolioImages,
                  onRemoveExisting: (id) {
                    setState(() => _removedExistingIds.add(id));
                  },
                  onRemovePending: (index) {
                    setState(() => _pendingImages.removeAt(index));
                  },
                ),

                const SizedBox(height: 24),

                // Hourly Rate Field
                const Text(
                  r'Your Fixed Hourly Price (₹/hr or $/hr)',
                  style: TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),
                _buildTextField(
                  controller: _priceController,
                  hintText: 'e.g. 150',
                  prefixIcon: Icons.payments_outlined,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) {
                      return 'Hourly price is required.';
                    }
                    if (double.tryParse(val) == null) {
                      return 'Please enter a valid numeric price.';
                    }
                    return null;
                  },
                ),

                const SizedBox(height: 24),

                // Experience Field
                const Text(
                  'Years of Experience',
                  style: TextStyle(
                    color: Color(0xFF1E212D),
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),
                _buildTextField(
                  controller: _experienceController,
                  hintText: 'e.g. 3',
                  prefixIcon: Icons.history_edu_outlined,
                  keyboardType: TextInputType.number,
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) {
                      return 'Years of experience is required.';
                    }
                    if (int.tryParse(val) == null) {
                      return 'Please enter an integer number.';
                    }
                    return null;
                  },
                ),

                const SizedBox(height: 48),

                // Submit Button
                GestureDetector(
                  onTap: _isLoading ? null : _handleSubmit,
                  child: Container(
                    height: 56,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: AppColors.lightPrimary,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.lightPrimary.withValues(alpha: 0.25),
                          blurRadius: 12,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Center(
                      child: _isLoading
                          ? const SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2.5,
                              ),
                            )
                          : Text(
                              _isEditing ? 'Save Changes' : 'Save and Continue',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String hintText,
    required IconData prefixIcon,
    TextInputType keyboardType = TextInputType.text,
    int maxLines = 1,
    String? Function(String?)? validator,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E6F2), width: 1.5),
      ),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        maxLines: maxLines,
        validator: validator,
        style: const TextStyle(
          color: Color(0xFF1E212D),
          fontSize: 15,
          fontWeight: FontWeight.w500,
        ),
        cursorColor: AppColors.lightPrimary,
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: const TextStyle(
            color: Color(0xFFA2A7B8),
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
          prefixIcon: Icon(
            prefixIcon,
            color: const Color(0xFFA2A7B8),
            size: 20,
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 18,
          ),
        ),
      ),
    );
  }
}
