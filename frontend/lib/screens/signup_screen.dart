import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import '../utils/constants.dart';
import '../utils/validators.dart';
import 'admin_dashboard.dart';
import 'customer_dashboard.dart';
import 'login_screen.dart';
import 'worker_dashboard.dart';

class SignupScreen extends StatefulWidget {
  final String initialRole;
  const SignupScreen({super.key, this.initialRole = 'customer'});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController(); // Full Name in UI
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _phoneController = TextEditingController();
  final _locationController = TextEditingController();
  
  late String _selectedRole;
  String? _apiError;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;

  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _selectedRole = widget.initialRole;

    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeIn),
    );

    _slideAnimation = Tween<Offset>(begin: const Offset(0.0, 0.08), end: Offset.zero).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeOut),
    );

    _fadeController.forward();
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _phoneController.dispose();
    _locationController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  Future<void> _handleSignup() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _apiError = null;
    });

    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final success = await authProvider.signup(
      username: _usernameController.text.trim(),
      email: _emailController.text.trim(),
      password: _passwordController.text,
      role: _selectedRole,
      phoneNumber: _phoneController.text.trim().isEmpty ? null : _phoneController.text.trim(),
    );

    if (!mounted) return;

    if (success && authProvider.user != null) {
      final user = authProvider.user!;
      
      // Let's also patch the location to the user profile if they supplied one!
      // This is elegant because the signup API can handle location directly, or we can send it.
      // Wait, we updated SignupSerializer in the backend to create the user with the location field,
      // but AuthProvider's signup method doesn't pass the location parameter to AuthService.
      // Let's double check this: AuthProvider has:
      // Future<bool> signup({required String username, required String email, required String password, required String role, String? phoneNumber})
      // Wait! We should verify if we want to update AuthProvider's signup method to pass the location field to AuthService,
      // or if we can handle location directly.
      // Let's update `auth_provider.dart` and `auth_service.dart` to support sending the `location` field on registration!
      // But wait! Is it already supported if we pass it, or do we need to add the parameter?
      // Yes, we will modify `auth_provider.dart` and `auth_service.dart` to support the location parameter.
      // For now, let's complete the `signup_screen.dart` structure, and then update provider and service!
    } else {
      setState(() {
        _apiError = authProvider.errorMessage ?? 'Registration failed. Please check your information.';
      });
    }
  }

  // A refined signup submission that passes the location field!
  Future<void> _handleSignupWithLocation() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _apiError = null;
    });

    // Let's call the updated AuthProvider.signup including the location field!
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    
    // We will update AuthProvider and AuthService to support location, let's write the code here assuming it is updated!
    final success = await authProvider.signup(
      username: _usernameController.text.trim().replaceAll(' ', '_'),
      email: _emailController.text.trim(),
      password: _passwordController.text,
      role: _selectedRole,
      phoneNumber: _phoneController.text.trim(),
      location: _locationController.text.trim().isEmpty ? null : _locationController.text.trim(),
    );

    if (!mounted) return;

    if (success && authProvider.user != null) {
      final user = authProvider.user!;
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.stars, color: Colors.white),
              const SizedBox(width: 12),
              Text('Welcome, ${user.username}! Account created successfully.'),
            ],
          ),
          backgroundColor: AppColors.success,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );

      // Role-Based Access Routing
      Widget nextScreen;
      if (user.role == 'worker') {
        nextScreen = WorkerDashboard(user: user);
      } else if (user.role == 'admin') {
        nextScreen = AdminDashboard(user: user);
      } else {
        nextScreen = CustomerDashboard(user: user);
      }

      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => nextScreen),
        (route) => false,
      );
    } else {
      setState(() {
        _apiError = authProvider.errorMessage ?? 'Registration failed. Please check your information.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final authProvider = Provider.of<AuthProvider>(context);

    return Scaffold(
      backgroundColor: AppColors.lightBg,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: SlideTransition(
            position: _slideAnimation,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top Header / Back Button
                Padding(
                  padding: const EdgeInsets.only(left: 16, top: 12),
                  child: IconButton(
                    icon: const Icon(
                      Icons.arrow_back_ios_new,
                      color: AppColors.lightTextPrimary,
                      size: 22,
                    ),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ),

                // Main Content
                Expanded(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 24.0),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 20),

                          // Title & Subtitle
                          const Text(
                            'Register',
                            style: TextStyle(
                              color: AppColors.lightTextPrimary,
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                              letterSpacing: -0.5,
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Create your account',
                            style: TextStyle(
                              color: AppColors.lightTextSecondary,
                              fontSize: 16,
                              fontWeight: FontWeight.w500,
                            ),
                          ),

                          const SizedBox(height: 32),

                          // Sliding Tabs
                          Container(
                            height: 48,
                            width: double.infinity,
                            decoration: const BoxDecoration(
                              border: Border(
                                bottom: BorderSide(
                                  color: AppColors.lightBorder,
                                  width: 1.5,
                                ),
                              ),
                            ),
                            child: Stack(
                              children: [
                                AnimatedAlign(
                                  duration: const Duration(milliseconds: 250),
                                  curve: Curves.easeInOut,
                                  alignment: _selectedRole == 'customer'
                                      ? Alignment.bottomLeft
                                      : Alignment.bottomRight,
                                  child: Container(
                                    width: size.width * 0.44,
                                    height: 3,
                                    color: AppColors.lightPrimary,
                                  ),
                                ),
                                Row(
                                  children: [
                                    Expanded(
                                      child: MouseRegion(
                                        cursor: SystemMouseCursors.click,
                                        child: GestureDetector(
                                          behavior: HitTestBehavior.opaque,
                                          onTap: () => setState(() => _selectedRole = 'customer'),
                                          child: Center(
                                            child: Text(
                                              'Customer',
                                              style: TextStyle(
                                                color: _selectedRole == 'customer'
                                                    ? AppColors.lightPrimary
                                                    : AppColors.lightTextHint,
                                                fontSize: 16,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                    Expanded(
                                      child: MouseRegion(
                                        cursor: SystemMouseCursors.click,
                                        child: GestureDetector(
                                          behavior: HitTestBehavior.opaque,
                                          onTap: () => setState(() => _selectedRole = 'worker'),
                                          child: Center(
                                            child: Text(
                                              'Worker',
                                              style: TextStyle(
                                                color: _selectedRole == 'worker'
                                                    ? AppColors.lightPrimary
                                                    : AppColors.lightTextHint,
                                                fontSize: 16,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 32),

                          // Error Banner
                          if (_apiError != null) ...[
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                              decoration: BoxDecoration(
                                color: AppColors.error.withOpacity(0.08),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: AppColors.error.withOpacity(0.3), width: 1),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.error_outline, color: AppColors.error, size: 20),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(
                                      _apiError!,
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

                          // Full Name Field (username)
                          _buildTextField(
                            controller: _usernameController,
                            hintText: 'Full Name',
                            prefixIcon: Icons.person_outline,
                            validator: Validators.validateUsername,
                          ),

                          const SizedBox(height: 20),

                          // Phone Number Field
                          _buildTextField(
                            controller: _phoneController,
                            hintText: 'Phone Number',
                            prefixIcon: Icons.phone_outlined,
                            keyboardType: TextInputType.phone,
                            validator: Validators.validatePhoneNumber,
                          ),

                          const SizedBox(height: 20),

                          // Email Address Field
                          _buildTextField(
                            controller: _emailController,
                            hintText: 'Email Address',
                            prefixIcon: Icons.email_outlined,
                            keyboardType: TextInputType.emailAddress,
                            validator: Validators.validateEmail,
                          ),

                          const SizedBox(height: 20),

                          // Password Field
                          _buildTextField(
                            controller: _passwordController,
                            hintText: 'Password',
                            prefixIcon: Icons.lock_outline,
                            isPassword: true,
                            obscureText: _obscurePassword,
                            onTogglePassword: () {
                              setState(() {
                                _obscurePassword = !_obscurePassword;
                              });
                            },
                            validator: Validators.validatePassword,
                          ),

                          const SizedBox(height: 20),

                          // Confirm Password Field
                          _buildTextField(
                            controller: _confirmPasswordController,
                            hintText: 'Confirm Password',
                            prefixIcon: Icons.lock_outline,
                            isPassword: true,
                            obscureText: _obscureConfirmPassword,
                            onTogglePassword: () {
                              setState(() {
                                _obscureConfirmPassword = !_obscureConfirmPassword;
                              });
                            },
                            validator: (val) => Validators.validateConfirmPassword(
                              val,
                              _passwordController.text,
                            ),
                          ),

                          const SizedBox(height: 20),

                          // Location Field
                          _buildTextField(
                            controller: _locationController,
                            hintText: 'Location',
                            prefixIcon: Icons.location_on_outlined,
                            validator: (val) {
                              if (val == null || val.trim().isEmpty) {
                                return 'Location is required';
                              }
                              return null;
                            },
                          ),

                          const SizedBox(height: 32),

                          // Register Button
                          // Register Button
                          MouseRegion(
                            cursor: SystemMouseCursors.click,
                            child: GestureDetector(
                              onTap: authProvider.isLoading ? null : _handleSignupWithLocation,
                              child: Container(
                                height: 56,
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  color: AppColors.lightPrimary,
                                  borderRadius: BorderRadius.circular(16),
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.lightPrimary.withOpacity(0.25),
                                      blurRadius: 12,
                                      offset: const Offset(0, 6),
                                    ),
                                  ],
                                ),
                                child: Center(
                                  child: authProvider.isLoading
                                      ? const SizedBox(
                                          width: 24,
                                          height: 24,
                                          child: CircularProgressIndicator(
                                            color: Colors.white,
                                            strokeWidth: 2.5,
                                          ),
                                        )
                                      : const Text(
                                          'Register',
                                          style: TextStyle(
                                            color: Colors.white,
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: 24),

                          // Footer / Switch to Login
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Text(
                                'Already have an account? ',
                                style: TextStyle(
                                  color: AppColors.lightTextSecondary,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              MouseRegion(
                                cursor: SystemMouseCursors.click,
                                child: GestureDetector(
                                  onTap: () {
                                    Navigator.of(context).pushReplacement(
                                      MaterialPageRoute(
                                        builder: (_) => const LoginScreen(),
                                      ),
                                    );
                                  },
                                  child: const Text(
                                    'Login',
                                    style: TextStyle(
                                      color: AppColors.lightPrimary,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 40),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// Helper to build text fields matching the styled border/container in Screenshots
  Widget _buildTextField({
    required TextEditingController controller,
    required String hintText,
    required IconData prefixIcon,
    bool isPassword = false,
    bool obscureText = false,
    VoidCallback? onTogglePassword,
    TextInputType keyboardType = TextInputType.text,
    String? Function(String?)? validator,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.lightInputFill,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.lightBorder,
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.015),
            blurRadius: 6,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: TextFormField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        validator: validator,
        style: const TextStyle(
          color: AppColors.lightTextPrimary,
          fontSize: 15,
          fontWeight: FontWeight.w500,
        ),
        cursorColor: AppColors.lightPrimary,
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: const TextStyle(
            color: AppColors.lightTextHint,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
          prefixIcon: Icon(
            prefixIcon,
            color: AppColors.lightTextHint,
            size: 20,
          ),
          suffixIcon: isPassword
              ? GestureDetector(
                  onTap: onTogglePassword,
                  child: Icon(
                    obscureText ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                    color: AppColors.lightTextHint,
                    size: 20,
                  ),
                )
              : null,
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
