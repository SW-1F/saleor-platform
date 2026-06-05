"""
Mock de uso de cupones (vouchers) para pruebas/demo.

Marca algunos códigos de voucher con `used > 0` para que el botón
"Mostrar cupones que han tenido uso" del dashboard tenga datos que mostrar.

Funciona igual sin importar cómo corras la API, porque se ejecuta a través de
`manage.py shell` (la redirección `<` la hace tu shell del host).

Uso:

  # A) Con docker-compose.full.yml (todo en Docker):
  docker compose -f docker-compose.full.yml run --rm api \
    python3 manage.py shell < scripts/mock_voucher_usage.py

  # B) Con el compose normal (solo infra) + API nativa (poetry/uv),
  #    ejecutándolo desde la carpeta del core `saleor/`:
  python manage.py shell < ../scripts/mock_voucher_usage.py

Requisito: que ya existan vouchers (p. ej. tras `manage.py populatedb`).
"""

from saleor.discount.models import VoucherCode

# Cuántos códigos marcar y con cuántos usos cada uno.
USAGE_VALUES = [4, 8, 2]

codes = list(VoucherCode.objects.order_by("id")[: len(USAGE_VALUES)])

if not codes:
    print(
        "No hay vouchers en la base de datos. "
        "Corre primero `manage.py populatedb` y vuelve a ejecutar este script."
    )
else:
    print("Marcando códigos de cupón con uso > 0:")
    for code, used in zip(codes, USAGE_VALUES):
        code.used = used
        code.save(update_fields=["used"])
        print(f"  {code.code} -> used = {code.used}")
    print(f"Listo: {len(codes)} código(s) de cupón con uso > 0.")
