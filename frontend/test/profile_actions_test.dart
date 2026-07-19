import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/user_model.dart';
import 'package:frontend/screens/profile_screen.dart';
import 'package:frontend/services/auth_provider.dart';
import 'package:provider/provider.dart';

void main() {
  testWidgets('customer profile actions open their feature screens', (
    tester,
  ) async {
    const user = UserModel(
      id: 7,
      username: 'test',
      email: 'test@gmail.com',
      role: 'customer',
    );

    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(home: ProfileScreen(initialUser: user)),
      ),
    );

    expect(find.text('Edit Profile'), findsOneWidget);
    expect(find.text('Change Password'), findsOneWidget);
    expect(find.text('Help & Support'), findsOneWidget);
    expect(find.text('Edit Profile Details'), findsNothing);
    expect(find.text('Worker Profile'), findsNothing);

    await tester.ensureVisible(find.text('Edit Profile'));
    await tester.tap(find.text('Edit Profile'));
    await tester.pumpAndSettle();
    expect(find.text('Save Changes'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Change Password'));
    await tester.tap(find.text('Change Password'));
    await tester.pumpAndSettle();
    expect(find.text('Update Password'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Help & Support'));
    await tester.tap(find.text('Help & Support'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 600));
    expect(find.text('Submit a Ticket'), findsOneWidget);
    await tester.ensureVisible(find.text('Submit Ticket'));
    expect(find.text('Submit Ticket'), findsOneWidget);
  });
}
