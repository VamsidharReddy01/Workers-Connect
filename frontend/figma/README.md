# Workers Bridge Code Connect Templates

These `.figma.ts` files map the UI pages in the supplied Workers Bridge reference to the Flutter app in `frontend/lib`.

Before publishing the mappings, replace each `url=TODO` line with the published Figma component URL for that screen or component. The URL must include `node-id`.

Implemented app mappings:

- `WelcomeScreen.figma.ts` -> `lib/screens/welcome_screen.dart`
- `LoginScreen.figma.ts` -> `lib/screens/login_screen.dart`
- `SignupScreen.figma.ts` -> `lib/screens/signup_screen.dart`
- `CustomerDashboard.figma.ts` -> `lib/screens/customer_dashboard.dart`
- `MainNavigation.figma.ts` -> `lib/screens/main_navigation.dart`
- `WorkerDashboard.figma.ts` -> `lib/screens/worker_dashboard.dart`
- `WorkerProfileSetupScreen.figma.ts` -> `lib/screens/worker_profile_setup_screen.dart`
- `BookingsScreen.figma.ts` -> `lib/screens/bookings_screen.dart`
- `MessagesScreen.figma.ts` -> `lib/screens/messages_screen.dart`
- `ProfileScreen.figma.ts` -> `lib/screens/profile_screen.dart`
- `CustomButton.figma.ts` -> `lib/widgets/custom_button.dart`
- `CustomTextField.figma.ts` -> `lib/widgets/custom_text_field.dart`
- `RoleSelector.figma.ts` -> `lib/widgets/role_selector.dart`

Reference screens that are still placeholders or not implemented in Dart are tracked in `MissingWorkerFlows.figma.ts`: worker list, worker details, book service, booking details, wallet, and rate review.
