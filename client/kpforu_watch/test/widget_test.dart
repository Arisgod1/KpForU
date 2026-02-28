import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:kpforu_watch/src/app.dart';

void main() {
  testWidgets('app renders', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: KpForUWatchApp()));
    expect(find.byType(KpForUWatchApp), findsOneWidget);
  });
}
