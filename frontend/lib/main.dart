import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'firebase_options.dart';
import 'services/auth_provider.dart';
import 'utils/app_routes.dart';
import 'utils/constants.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // Avoid fetching fonts from fonts.gstatic.com (fails offline / blocked networks).
  if (kIsWeb) {
    GoogleFonts.config.allowRuntimeFetching = false;
  }

  if (kDebugMode) {
    debugPrint('API base: ${ApiConstants.serverBaseUrl}');
    debugPrint('Login: ${ApiConstants.loginEndpoint}');
  }
  runApp(const WorkersConnectApp());
}

TextTheme _appTextTheme(Brightness brightness) {
  final base = brightness == Brightness.dark
      ? ThemeData.dark().textTheme
      : ThemeData.light().textTheme;
  // Outfit is loaded from CDN by google_fonts; on web use bundled/system fonts.
  if (kIsWeb) {
    return base;
  }
  return GoogleFonts.outfitTextTheme(base);
}

class WorkersConnectApp extends StatelessWidget {
  const WorkersConnectApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider(),
      child: MaterialApp(
        title: 'Workers Connect',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.dark,
          scaffoldBackgroundColor: AppColors.primaryDark,
          colorScheme: ColorScheme.fromSeed(
            seedColor: AppColors.accentViolet,
            brightness: Brightness.dark,
            primary: AppColors.accentViolet,
            secondary: AppColors.accentBlue,
            error: AppColors.error,
          ),
          textTheme: _appTextTheme(Brightness.dark),
        ),
        initialRoute: AppRoutes.splash,
        routes: AppRoutes.routes,
      ),
    );
  }
}
