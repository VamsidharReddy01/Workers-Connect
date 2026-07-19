import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../models/user_model.dart';
import '../../services/firebase_phone_auth_service.dart';
import '../../utils/auth_navigation.dart';
import '../../utils/constants.dart';
import '../../utils/validators.dart';

class OtpVerificationScreen extends StatefulWidget {
  final String phoneNumber;
  final String verificationId;
  final int? resendToken;

  const OtpVerificationScreen({
    super.key,
    required this.phoneNumber,
    required this.verificationId,
    this.resendToken,
  });

  @override
  State<OtpVerificationScreen> createState() => _OtpVerificationScreenState();
}

class _OtpVerificationScreenState extends State<OtpVerificationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _otpController = TextEditingController();
  final FirebasePhoneAuthService _phoneAuthService = FirebasePhoneAuthService();

  bool _isLoading = false;
  bool _isResending = false;
  late String _verificationId;
  int? _resendToken;

  @override
  void initState() {
    super.initState();
    _verificationId = widget.verificationId;
    _resendToken = widget.resendToken;
  }

  @override
  void dispose() {
    _otpController.dispose();
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
    _showSnackBar('Phone number verified successfully!', isError: false);
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
      _showSnackBar(e.message ?? 'Verification failed.');
    } catch (_) {
      _showSnackBar('Verification failed. Please try again.');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _verifyOtp() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final credentialResult = await _phoneAuthService.verifyOtp(
        verificationId: _verificationId,
        smsCode: _otpController.text.trim(),
      );
      final user = credentialResult.user;
      if (user != null) {
        await _completeSignIn(user);
      } else {
        _showSnackBar('Sign-in failed. Please try again.');
      }
    } on FirebaseAuthException catch (e) {
      _showSnackBar(e.message ?? 'Invalid OTP. Please try again.');
    } catch (_) {
      _showSnackBar('Verification failed. Please try again.');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _resendOtp() async {
    setState(() => _isResending = true);

    await _phoneAuthService.sendOtp(
      phoneNumber: widget.phoneNumber,
      forceResendingToken: _resendToken,
      onCodeSent: (verificationId, resendToken) {
        if (!mounted) return;
        setState(() {
          _verificationId = verificationId;
          _resendToken = resendToken;
          _isResending = false;
        });
        _showSnackBar('A new OTP has been sent.', isError: false);
      },
      onVerificationFailed: (FirebaseAuthException e) {
        print("=================================");
        print("FIREBASE PHONE AUTH ERROR");
        print("Code: ${e.code}");
        print("Message: ${e.message}");
        print("=================================");
        if (!mounted) return;
        setState(() => _isResending = false);
        _showSnackBar(e.message ?? 'Failed to resend OTP. Please try again.');
      },
      onVerificationCompleted: (credential) {
        _handleAutoVerification(credential);
      },
      onCodeAutoRetrievalTimeout: (verificationId) {
        if (!mounted) return;
        setState(() => _verificationId = verificationId);
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
    final maskedPhone = _maskPhoneNumber(widget.phoneNumber);

    return Scaffold(
      backgroundColor: AppColors.lightBg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: AppColors.lightTextPrimary,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(
                    Icons.sms_outlined,
                    size: 64,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Verify OTP',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppColors.lightTextPrimary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Enter the ${AuthConstants.otpLength}-digit code sent to $maskedPhone',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: AppColors.lightTextSecondary,
                    ),
                  ),
                  const SizedBox(height: 32),
                  TextFormField(
                    controller: _otpController,
                    enabled: !_isLoading,
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 24,
                      letterSpacing: 8,
                      fontWeight: FontWeight.bold,
                    ),
                    inputFormatters: [
                      FilteringTextInputFormatter.digitsOnly,
                      LengthLimitingTextInputFormatter(AuthConstants.otpLength),
                    ],
                    validator: Validators.validateOtp,
                    decoration: InputDecoration(
                      labelText: 'OTP',
                      hintText: '0' * AuthConstants.otpLength,
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
                    onPressed: _isLoading ? null : _verifyOtp,
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
                            'Verify & Sign In',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: (_isLoading || _isResending) ? null : _resendOtp,
                    child: _isResending
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Resend OTP'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _maskPhoneNumber(String phone) {
    if (phone.length < 4) return phone;
    final visible = phone.substring(phone.length - 4);
    return '******$visible';
  }
}
