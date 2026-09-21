import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/main.dart';

void main() {
  testWidgets('Abre en la Home pública, no en Login', (WidgetTester tester) async {
    await tester.pumpWidget(const FashionStoreApp());

    // "FASHIONSTORE" aparece tanto en el header como en el hero (fallback
    // sin colección destacada) -- ambos son comportamiento real esperado.
    expect(find.text('FASHIONSTORE'), findsWidgets);
    expect(find.text('Inicio'), findsWidgets);
  });
}
