"""CU30 -- Consultar reportes e indicadores (Administrador), PK06.

PRIMERA PARTE: dashboard analítico real sobre PostgreSQL. Sin comando de
voz, sin Gemini, sin consultas IA, sin resumen del Encargado -- eso queda
para una fase posterior (ver docstring de service.py). Todo lo que expone
este módulo hoy son reportes REALES agregados en FastAPI/PostgreSQL, nunca
datos inventados ni calculados en Angular.

Puramente CONSULTIVO -- ningún archivo de este paquete modifica Venta,
Pago, StockSucursal, Reserva, DevolucionCambio ni Promocion. Reutiliza esos
modelos tal cual los definieron sus CU dueños (P1/P4/P5/P6), nunca duplica
sus reglas de negocio ni sus tablas.

Arquitectura obligatoria, igual que el resto del proyecto:

    Angular -> FastAPI (router.py) -> service.py -> repository.py -> PostgreSQL

Preparado para una fase futura de voz/IA (NO implementada aún): esa fase
deberá reutilizar EXACTAMENTE estos mismos ReportesService/repositorios
-- interpretar la intención con Gemini y llamar a los mismos métodos que ya
usa el dashboard, nunca una segunda lógica de reportes en paralelo.
"""
