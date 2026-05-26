import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';

void main() {
  testWidgets('Splash Screen Smoke Test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const WorkersConnectApp());

    // Verify that the title 'Workers Connect' is displayed on the splash screen
    expect(find.text('Workers Connect'), findsOneWidget);
    expect(find.text('Connecting Services Instantly'), findsOneWidget);

    // Advance the virtual clock by 2 seconds to let the timer complete
    await tester.pump(const Duration(seconds: 2));
  });
}
