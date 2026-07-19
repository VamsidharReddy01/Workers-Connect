import 'package:flutter/material.dart';

import '../models/user_model.dart';
import '../screens/admin_dashboard.dart';
import '../screens/main_navigation.dart';
import '../screens/worker_dashboard.dart';

/// Shared navigation helpers after authentication.
class AuthNavigation {
  AuthNavigation._();

  static Widget homeForUser(UserModel user) {
    if (user.role == 'worker') {
      return WorkerDashboard(user: user);
    }
    if (user.role == 'admin') {
      return AdminDashboard(user: user);
    }
    return MainNavigation(user: user);
  }

  static void goHome(BuildContext context, UserModel user) {
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => homeForUser(user)),
      (_) => false,
    );
  }
}
