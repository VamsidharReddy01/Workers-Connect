import 'package:flutter/material.dart';

import '../screens/splash_screen.dart';

/// Named route constants and route table for the app.
class AppRoutes {
  AppRoutes._();

  static const String splash = '/';

  static Map<String, WidgetBuilder> get routes => {
    splash: (_) => const SplashScreen(),
  };
}
