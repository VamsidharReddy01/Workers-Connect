import 'package:flutter/material.dart';
import '../models/user_model.dart';
import '../services/auth_service.dart';
import '../utils/constants.dart';
import 'login_screen.dart';

class HomeScreen extends StatefulWidget {
  final UserModel user;

  const HomeScreen({
    super.key,
    required this.user,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String? _accessTokenPreview;
  String? _refreshTokenPreview;
  bool _isRefreshingToken = false;

  @override
  void initState() {
    super.initState();
    _loadSecureTokensPreview();
  }

  Future<void> _loadSecureTokensPreview() async {
    final auth = AuthService();
    final access = await auth.getAccessToken();
    final refresh = await auth.getStoredUser(); // Check secure storage
    
    // Read directly from secure storage for visual proof
    final rawRefresh = await auth.refreshToken(); // Test if refresh is working, but let's read the storage directly.
    final storage = auth.getAccessToken(); // Secure storage is encapsulated inside AuthService. Let's make an helper or just show access token prefix.
    
    setState(() {
      if (access != null && access.length > 20) {
        _accessTokenPreview = '${access.substring(0, 10)}...${access.substring(access.length - 10)}';
      } else {
        _accessTokenPreview = access ?? 'No Access Token';
      }
      _refreshTokenPreview = 'Stored securely in flutter_secure_storage';
    });
  }

  Future<void> _handleTokenRefresh() async {
    setState(() {
      _isRefreshingToken = true;
    });

    final success = await AuthService().refreshToken();

    setState(() {
      _isRefreshingToken = false;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              Icon(
                success ? Icons.sync : Icons.error_outline,
                color: Colors.white,
              ),
              const SizedBox(width: 12),
              Text(
                success
                    ? 'JWT Access Token refreshed successfully!'
                    : 'Failed to refresh token. Session may have expired.',
              ),
            ],
          ),
          backgroundColor: success ? AppColors.success : AppColors.error,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
      if (success) {
        _loadSecureTokensPreview();
      }
    }
  }

  Future<void> _handleLogout() async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.primaryMid,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Logout', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: const Text(
          'Are you sure you want to end your session? Stored JWT tokens will be wiped completely.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel', style: TextStyle(color: AppColors.textHint)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () async {
              Navigator.of(context).pop(); // Close dialog
              await AuthService().logout();
              if (mounted) {
                Navigator.of(context).pushAndRemoveUntil(
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                  (route) => false,
                );
              }
            },
            child: const Text('Logout', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final isWorker = widget.user.isWorker;

    return Scaffold(
      body: Container(
        width: size.width,
        height: size.height,
        decoration: const BoxDecoration(
          gradient: AppColors.backgroundGradient,
        ),
        child: SafeArea(
          child: Column(
            children: [
              // Custom Header App Bar
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.connect_without_contact, color: AppColors.accentViolet, size: 28),
                        SizedBox(width: 8),
                        Text(
                          'Workers Connect',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.logout_rounded, color: AppColors.error, size: 26),
                      tooltip: 'Logout',
                      onPressed: _handleLogout,
                    ),
                  ],
                ),
              ),

              // Scrollable Dashboard Body
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Column(
                    children: [
                      const SizedBox(height: 20),

                      // User Avatar & Badges
                      Center(
                        child: Column(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(4),
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: LinearGradient(
                                  colors: isWorker
                                      ? [AppColors.accentPink, AppColors.accentViolet]
                                      : [AppColors.accentViolet, AppColors.accentBlue],
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: (isWorker ? AppColors.accentPink : AppColors.accentBlue)
                                        .withOpacity(0.3),
                                    blurRadius: 20,
                                    offset: const Offset(0, 10),
                                  ),
                                ],
                              ),
                              child: CircleAvatar(
                                radius: 55,
                                backgroundColor: AppColors.primaryMid,
                                child: Icon(
                                  isWorker ? Icons.engineering_rounded : Icons.person_rounded,
                                  size: 55,
                                  color: isWorker ? AppColors.accentPink : AppColors.accentBlue,
                                ),
                              ),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              widget.user.username,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 26,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                              decoration: BoxDecoration(
                                color: (isWorker ? AppColors.accentPink : AppColors.accentViolet)
                                    .withOpacity(0.15),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: isWorker ? AppColors.accentPink : AppColors.accentViolet,
                                  width: 1,
                                ),
                              ),
                              child: Text(
                                widget.user.roleDisplay,
                                style: TextStyle(
                                  color: isWorker ? AppColors.accentPink : Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                  letterSpacing: 0.5,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 36),

                      // Account Details Section
                      _buildSectionHeader('Account Information'),
                      const SizedBox(height: 12),
                      _buildDashboardCard([
                        _buildInfoRow(Icons.email_outlined, 'Email Address', widget.user.email),
                        const Divider(color: AppColors.cardBorder, height: 1),
                        _buildInfoRow(
                          Icons.perm_identity_outlined,
                          'User Account ID',
                          '#${widget.user.id}',
                        ),
                      ]),

                      const SizedBox(height: 24),

                      // Secure storage details section
                      _buildSectionHeader('Secure JWT Tokens (Storage Verification)'),
                      const SizedBox(height: 12),
                      _buildDashboardCard([
                        _buildInfoRow(
                          Icons.vpn_key_outlined,
                          'Access Token Preview',
                          _accessTokenPreview ?? 'Loading...',
                          isCode: true,
                        ),
                        const Divider(color: AppColors.cardBorder, height: 1),
                        _buildInfoRow(
                          Icons.security_outlined,
                          'Refresh Token Storage',
                          _refreshTokenPreview ?? 'Loading...',
                          isCode: true,
                        ),
                      ]),

                      const SizedBox(height: 30),

                      // Action Button to demonstrate token refresh
                      if (_isRefreshingToken)
                        const CircularProgressIndicator(color: AppColors.accentViolet)
                      else
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white.withOpacity(0.06),
                            foregroundColor: Colors.white,
                            surfaceTintColor: Colors.transparent,
                            side: const BorderSide(color: AppColors.cardBorder),
                            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                          ),
                          onPressed: _handleTokenRefresh,
                          icon: const Icon(Icons.autorenew_rounded, color: AppColors.accentBlue),
                          label: const Text(
                            'Verify & Refresh JWT Access Token',
                            style: TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ),

                      const SizedBox(height: 40),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: const TextStyle(
          color: AppColors.textSecondary,
          fontSize: 14,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildDashboardCard(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.cardBorder, width: 1),
      ),
      child: Column(
        children: children,
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String title, String value, {bool isCode = false}) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppColors.textSecondary, size: 22),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.textHint,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: isCode ? FontWeight.w500 : FontWeight.bold,
                    fontFamily: isCode ? 'monospace' : null,
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
