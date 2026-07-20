# Plan de regresión de backend

## Entrada

- Dependencias instaladas desde `requirements.txt`.
- Puertos dinámicos disponibles para servicios temporales.
- No requiere Docker, frontend ni n8n.

## Ejecución obligatoria

1. `make regression`: cobertura mínima de 80% e integración HTTP completa.
2. `python scripts/stress_check.py`: escenarios de 50 y 100 ventas.
3. `docker compose config --quiet`: validación de la definición de despliegue.

## Criterios de salida

- Cero pruebas unitarias o de contrato fallidas.
- Cobertura de líneas y ramas igual o superior a 80%.
- Recorrido prospecto → venta → seguro → métricas aprobado.
- Cero errores en los escenarios de 50 y 100 ventas.
- p95 menor a 2.000 ms para 100 ventas simultáneas.
- Reporte con CPU pico y memoria pico disponible.

Una falla en cualquiera de estos criterios bloquea la entrega del backend.
