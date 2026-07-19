import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../models/user_model.dart';
import '../../services/firebase_phone_auth_service.dart';
import '../../utils/auth_navigation.dart';
import '../../utils/constants.dart';
import '../../utils/validators.dart';
import 'otp_verification_screen.dart';

class PhoneLoginScreen extends StatefulWidget {
  const PhoneLoginScreen({super.key});

  @override
  State<PhoneLoginScreen> createState() => _PhoneLoginScreenState();
}

class _PhoneLoginScreenState extends State<PhoneLoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final FirebasePhoneAuthService _phoneAuthService = FirebasePhoneAuthService();

  bool _isLoading = false;

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  void _showSnackBar(String message, {bool isError = true}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: isError ? AppColors.error : AppColors.success,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      );
  }

  Future<void> _completeSignIn(User user) async {
    final appUser = UserModel.fromFirebaseUser(user);
    if (!mounted) return;
    _showSnackBar('Welcome to Workers Bridge!', isError: false);
    AuthNavigation.goHome(context, appUser);
  }

  Future<void> _handleAutoVerification(PhoneAuthCredential credential) async {
    setState(() => _isLoading = true);
    try {
      final credentialResult = await _phoneAuthService.signInWithCredential(
        credential,
      );
      final user = credentialResult.user;
      if (user != null) {
        await _completeSignIn(user);
      } else {
        _showSnackBar('Sign-in failed. Please try again.');
      }
    } on FirebaseAuthException catch (e) {
      _showSnackBar(e.message ?? 'Automatic verification failed.');
    } catch (_) {
      _showSnackBar('Automatic verification failed. Please try again.');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _sendOtp() async {
    if (!_formKey.currentState!.validate()) return;

    final e164Phone = Validators.formatIndianPhoneE164(
      _phoneController.text.trim(),
    );

    setState(() => _isLoading = true);

    await _phoneAuthService.sendOtp(
      phoneNumber: e164Phone,
      onCodeSent: (verificationId, resendToken) {
        if (!mounted) return;
        setState(() => _isLoading = false);
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => OtpVerificationScreen(
              phoneNumber: e164Phone,
              verificationId: verificationId,
              resendToken: resendToken,
            ),
          ),
        );
      },
      onVerificationFailed: (FirebaseAuthException e) {
        print("=================================");
        print("FIREBASE PHONE AUTH ERROR");
        print("Code: ${e.code}");
        print("Message: ${e.message}");
        print("=================================");
        if (!mounted) return;
        setState(() => _isLoading = false);
        _showSnackBar(
          e.message ?? 'Phone verification failed. Please try again.',
        );
      },
      onVerificationCompleted: (credential) {
        _handleAutoVerification(credential);
      },
      onCodeAutoRetrievalTimeout: (verificationId) {
        if (!mounted) return;
        _showSnackBar(
          'OTP auto-retrieval timed out. Enter the code manually.',
          isError: false,
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: AppColors.lightBg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(
                    Icons.phone_android_rounded,
                    size: 64,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Sign in with Phone',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppColors.lightTextPrimary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Enter your Indian mobile number to receive a one-time password.',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: AppColors.lightTextSecondary,
                    ),
                  ),
                  const SizedBox(height: 32),
                  TextFormField(
                    controller: _phoneController,
                    enabled: !_isLoading,
                    keyboardType: TextInputType.phone,
                    inputFormatters: [
                      FilteringTextInputFormatter.digitsOnly,
                      LengthLimitingTextInputFormatter(12),
                    ],
                    validator: Validators.validateIndianPhoneNumber,
                    decoration: InputDecoration(
                      labelText: 'Mobile number',
                      hintText: '9876543210',
                      prefixIcon: const Icon(Icons.phone_outlined),
                      prefixText: '${AuthConstants.indiaCountryCode} ',
                      filled: true,
                      fillColor: AppColors.lightInputFill,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: const BorderSide(
                          color: AppColors.lightBorder,
                        ),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: const BorderSide(
                          color: AppColors.lightBorder,
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(
                          color: theme.colorScheme.primary,
                          width: 2,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: _isLoading ? null : _sendOtp,
                    style: FilledButton.styleFrom(
                      minimumSize: const Size.fromHeight(52),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            'Send OTP',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
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
}
