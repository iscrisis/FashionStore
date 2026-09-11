import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/main.dart';

void main() {
  testWidgets('Muestra la pantalla de prueba de conexión con FastAPI',
      (WidgetTester tester) async {
    await tester.pumpWidget(const FashionStoreApp());

    expect(find.text('Prueba de conexión FastAPI'), findsOneWidget);
  });
}
