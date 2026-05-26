import 'package:flutter/material.dart';
import '../utils/constants.dart';
import 'login_screen.dart';
import 'signup_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: AppColors.lightBg,
      body: SafeArea(
        child: Stack(
          children: [
            // Ambient glowing circles in background
            Positioned(
              top: -80,
              left: -80,
              child: Container(
                width: 260,
                height: 260,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.lightPrimary.withOpacity(0.08),
                ),
              ),
            ),
            Positioned(
              top: size.height * 0.15,
              right: -100,
              child: Container(
                width: 300,
                height: 300,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.lightAccent.withOpacity(0.06),
                ),
              ),
            ),

            // Main Content Layout
            Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          const SizedBox(height: 60),

                          // High-fidelity Custom Vector Bridge Logo
                          SizedBox(
                            width: 220,
                            height: 140,
                            child: CustomPaint(
                              painter: BridgeLogoPainter(),
                            ),
                          ),
                          
                          const SizedBox(height: 12),
                          
                          // Brand Name
                          const Text(
                            'Workers',
                            style: TextStyle(
                              color: AppColors.lightTextPrimary,
                              fontSize: 34,
                              fontWeight: FontWeight.w800,
                              height: 1.1,
                              letterSpacing: -0.5,
                            ),
                          ),
                          const Text(
                            'Bridge',
                            style: TextStyle(
                              color: AppColors.lightPrimary,
                              fontSize: 34,
                              fontWeight: FontWeight.w800,
                              height: 1.0,
                              letterSpacing: -0.5,
                            ),
                          ),

                          const SizedBox(height: 28),

                          // Subtitle Text
                          const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 32.0),
                            child: Text(
                              'Find trusted workers\nfor your everyday needs',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: AppColors.lightTextSecondary,
                                fontSize: 16,
                                fontWeight: FontWeight.w500,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                // City Silhouette and Buttons Container
                Stack(
                  alignment: Alignment.bottomCenter,
                  children: [
                    // Styled skyline silhouette painter
                    Opacity(
                      opacity: 0.12,
                      child: Container(
                        height: 180,
                        width: double.infinity,
                        margin: const EdgeInsets.only(bottom: 120),
                        child: CustomPaint(
                          painter: SkylinePainter(),
                        ),
                      ),
                    ),

                    // Actions Panel
                    Padding(
                      padding: const EdgeInsets.fromLTRB(24, 20, 24, 30),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // Continue as Customer Button
                          MouseRegion(
                            cursor: SystemMouseCursors.click,
                            child: GestureDetector(
                              onTap: () {
                                Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) => const SignupScreen(initialRole: 'customer'),
                                  ),
                                );
                              },
                              child: Container(
                                height: 58,
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  color: AppColors.lightPrimary,
                                  borderRadius: BorderRadius.circular(16),
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.lightPrimary.withOpacity(0.3),
                                      blurRadius: 15,
                                      offset: const Offset(0, 6),
                                    ),
                                  ],
                                ),
                                child: const Center(
                                  child: Text(
                                    'Continue as Customer',
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

                          const SizedBox(height: 16),

                          // Continue as Worker Button
                          MouseRegion(
                            cursor: SystemMouseCursors.click,
                            child: GestureDetector(
                              onTap: () {
                                Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) => const SignupScreen(initialRole: 'worker'),
                                  ),
                                );
                              },
                              child: Container(
                                height: 58,
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(
                                    color: AppColors.lightPrimary,
                                    width: 1.8,
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.lightTextHint.withOpacity(0.05),
                                      blurRadius: 8,
                                      offset: const Offset(0, 4),
                                    ),
                                  ],
                                ),
                                child: const Center(
                                  child: Text(
                                    'Continue as Worker',
                                    style: TextStyle(
                                      color: AppColors.lightPrimary,
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: 24),

                          // Already have an account? Login
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
                                    Navigator.of(context).push(
                                      MaterialPageRoute(
                                        builder: (_) => const LoginScreen(),
                                      ),
                                    );
                                  },
                                  child: const Text(
                                    'Login',
                                    style: TextStyle(
                                      color: AppColors.lightPrimary,
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      decoration: TextDecoration.none,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Custom Painter to draw the premium "Workers Bridge" vector logo from Screenshot 1
class BridgeLogoPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // Draw the orange left figure
    final orangePaint = Paint()
      ..color = Colors.orange.shade600
      ..style = PaintingStyle.fill;
    
    // Left figure body
    final leftBodyPath = Path()
      ..moveTo(w * 0.18, h * 0.45)
      ..lineTo(w * 0.28, h * 0.45)
      ..lineTo(w * 0.26, h * 0.25)
      ..lineTo(w * 0.20, h * 0.25)
      ..close();
    canvas.drawPath(leftBodyPath, orangePaint);
    // Left figure head
    canvas.drawCircle(Offset(w * 0.23, h * 0.16), 7, orangePaint);

    // Draw the blue right figure
    final darkBluePaint = Paint()
      ..color = const Color(0xFF1E3A8A)
      ..style = PaintingStyle.fill;

    // Right figure body
    final rightBodyPath = Path()
      ..moveTo(w * 0.72, h * 0.45)
      ..lineTo(w * 0.82, h * 0.45)
      ..lineTo(w * 0.80, h * 0.25)
      ..lineTo(w * 0.74, h * 0.25)
      ..close();
    canvas.drawPath(rightBodyPath, darkBluePaint);
    // Right figure head
    canvas.drawCircle(Offset(w * 0.77, h * 0.16), 7, darkBluePaint);

    // Draw secondary blue figures
    final royalBluePaint = Paint()
      ..color = const Color(0xFF3444F4)
      ..style = PaintingStyle.fill;

    // Left auxiliary figure
    final leftAuxPath = Path()
      ..moveTo(w * 0.08, h * 0.52)
      ..lineTo(w * 0.16, h * 0.52)
      ..lineTo(w * 0.14, h * 0.38)
      ..lineTo(w * 0.10, h * 0.38)
      ..close();
    canvas.drawPath(leftAuxPath, royalBluePaint);
    canvas.drawCircle(Offset(w * 0.12, h * 0.32), 5, royalBluePaint);

    // Right auxiliary figure
    final rightAuxPath = Path()
      ..moveTo(w * 0.84, h * 0.52)
      ..lineTo(w * 0.92, h * 0.52)
      ..lineTo(w * 0.90, h * 0.38)
      ..lineTo(w * 0.86, h * 0.38)
      ..close();
    canvas.drawPath(rightAuxPath, royalBluePaint);
    canvas.drawCircle(Offset(w * 0.88, h * 0.32), 5, royalBluePaint);

    // Draw the Bridge arches connecting the figures
    final bridgePaint = Paint()
      ..color = const Color(0xFF3444F4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.5;

    // Upper bridge deck arch
    final upperBridgePath = Path()
      ..moveTo(w * 0.10, h * 0.45)
      ..quadraticBezierTo(w * 0.5, h * 0.22, w * 0.90, h * 0.45);
    canvas.drawPath(upperBridgePath, bridgePaint);

    // Lower support arch
    final lowerBridgePath = Path()
      ..moveTo(w * 0.12, h * 0.55)
      ..quadraticBezierTo(w * 0.5, h * 0.38, w * 0.88, h * 0.55);
    canvas.drawPath(lowerBridgePath, bridgePaint);

    // Draw vertical bridge support cables
    final cablePaint = Paint()
      ..color = const Color(0xFF3444F4).withOpacity(0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    for (int i = 1; i <= 7; i++) {
      double t = i / 8.0;
      double x = w * (0.12 + t * 0.76);
      
      // Calculate y values on the quadratic curves to draw clean vertical lines
      double t1 = 0.10 + t * 0.80;
      double yUpper = h * 0.45 + (1 - t1) * (1 - t1) * 0.0 + 2 * (1 - t1) * t1 * (h * 0.22 - h * 0.45);
      double yLower = h * 0.55 + (1 - t1) * (1 - t1) * 0.0 + 2 * (1 - t1) * t1 * (h * 0.38 - h * 0.55);

      canvas.drawLine(Offset(x, yUpper + 10), Offset(x, yLower + 12), cablePaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Custom Painter to draw a clean, vector styled city skyline background silhouette at the bottom of the welcome screen
class SkylinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    final paint = Paint()
      ..color = const Color(0xFF3444F4).withOpacity(0.18)
      ..style = PaintingStyle.fill;

    final path = Path()
      ..moveTo(0, h)
      ..lineTo(0, h * 0.70)
      ..lineTo(w * 0.06, h * 0.70)
      ..lineTo(w * 0.06, h * 0.65)
      ..lineTo(w * 0.12, h * 0.65)
      ..lineTo(w * 0.12, h * 0.80)
      ..lineTo(w * 0.18, h * 0.80)
      ..lineTo(w * 0.18, h * 0.50)
      ..lineTo(w * 0.24, h * 0.50)
      ..lineTo(w * 0.24, h * 0.55)
      ..lineTo(w * 0.30, h * 0.55)
      ..lineTo(w * 0.30, h * 0.85)
      ..lineTo(w * 0.34, h * 0.85)
      ..lineTo(w * 0.34, h * 0.40)
      ..lineTo(w * 0.42, h * 0.40)
      ..lineTo(w * 0.42, h * 0.75)
      ..lineTo(w * 0.48, h * 0.75)
      ..lineTo(w * 0.48, h * 0.30)
      ..lineTo(w * 0.54, h * 0.30)
      ..lineTo(w * 0.54, h * 0.35)
      ..lineTo(w * 0.60, h * 0.35)
      ..lineTo(w * 0.60, h * 0.70)
      ..lineTo(w * 0.68, h * 0.70)
      ..lineTo(w * 0.68, h * 0.48)
      ..lineTo(w * 0.74, h * 0.48)
      ..lineTo(w * 0.74, h * 0.60)
      ..lineTo(w * 0.80, h * 0.60)
      ..lineTo(w * 0.80, h * 0.80)
      ..lineTo(w * 0.86, h * 0.80)
      ..lineTo(w * 0.86, h * 0.55)
      ..lineTo(w * 0.94, h * 0.55)
      ..lineTo(w * 0.94, h * 0.72)
      ..lineTo(w * 1.0, h * 0.72)
      ..lineTo(w * 1.0, h)
      ..close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
