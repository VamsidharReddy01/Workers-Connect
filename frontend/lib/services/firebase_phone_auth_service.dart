import 'package:firebase_auth/firebase_auth.dart';

import '../utils/constants.dart';

/// Callback types for Firebase phone verification flow.
typedef PhoneCodeSentCallback =
    void Function(String verificationId, int? resendToken);

typedef PhoneVerificationFailedCallback =
    void Function(FirebaseAuthException exception);

typedef PhoneVerificationCompletedCallback =
    void Function(PhoneAuthCredential credential);

typedef PhoneCodeAutoRetrievalTimeoutCallback =
    void Function(String verificationId);

/// Reusable service for Firebase Phone Authentication.
class FirebasePhoneAuthService {
  FirebasePhoneAuthService({FirebaseAuth? auth})
    : _auth = auth ?? FirebaseAuth.instance;

  final FirebaseAuth _auth;

  /// Currently signed-in Firebase user, if any.
  User? get currentUser => _auth.currentUser;

  /// Whether a Firebase user session is active.
  bool get isSignedIn => currentUser != null;

  /// Sends an OTP to [phoneNumber] using Firebase [verifyPhoneNumber].
  Future<void> sendOtp({
    required String phoneNumber,
    required PhoneCodeSentCallback onCodeSent,
    required PhoneVerificationFailedCallback onVerificationFailed,
    required PhoneVerificationCompletedCallback onVerificationCompleted,
    required PhoneCodeAutoRetrievalTimeoutCallback onCodeAutoRetrievalTimeout,
    Duration timeout = AuthConstants.otpTimeout,
    int? forceResendingToken,
  }) async {
    await _auth.verifyPhoneNumber(
      phoneNumber: phoneNumber,
      timeout: timeout,
      forceResendingToken: forceResendingToken,
      verificationCompleted: onVerificationCompleted,
      verificationFailed: onVerificationFailed,
      codeSent: onCodeSent,
      codeAutoRetrievalTimeout: onCodeAutoRetrievalTimeout,
    );
  }

  /// Builds a [PhoneAuthCredential] from the verification ID and SMS code.
  PhoneAuthCredential buildCredential({
    required String verificationId,
    required String smsCode,
  }) {
    return PhoneAuthProvider.credential(
      verificationId: verificationId,
      smsCode: smsCode,
    );
  }

  /// Signs in with the given phone auth credential.
  Future<UserCredential> signInWithCredential(PhoneAuthCredential credential) {
    return _auth.signInWithCredential(credential);
  }

  /// Verifies the OTP and signs the user in.
  Future<UserCredential> verifyOtp({
    required String verificationId,
    required String smsCode,
  }) async {
    final credential = buildCredential(
      verificationId: verificationId,
      smsCode: smsCode,
    );
    return signInWithCredential(credential);
  }

  /// Signs out the current Firebase user.
  Future<void> signOut() => _auth.signOut();
}
