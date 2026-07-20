# Reporte final de pruebas de backend

## Alcance

La regresión cubre los microservicios de prospectos, ventas, seguros y métricas, la persistencia SQLite, la estructura de los scripts Oracle y los escenarios de carga. El frontend y la ejecución de workflows n8n quedan fuera de esta fase.

## Pruebas unitarias y de contrato

El 19 de julio de 2026 se ejecutaron 25 pruebas automatizadas. Todas aprobaron. La cobertura de líneas y ramas fue 91%, por encima del mínimo requerido de 80%.

La suite verifica validaciones, historial de etapas, cierre mediante venta, coherencia de vendedor, ventas fallidas, primas, seguros vinculados, conversión global, por vendedor y por etapa, integridad referencial, almacenamiento de rendimiento y contratos HTTP.

## Integración

`python scripts/integration_check.py --self-contained` inicia los cuatro servicios con una base temporal y verifica por HTTP:

1. Salud de cada servicio.
2. Lectura de catálogos.
3. Registro y avance de un prospecto.
4. Registro de venta efectiva.
5. Vinculación de seguro vendido.
6. Consolidación de indicadores y conversiones.
7. Eliminación de los datos temporales.

El recorrido completo aprobó sin errores.

## Estrés y recursos

`python scripts/stress_check.py` ejecuta ambos escenarios en servicios temporales. La preparación de prospectos queda fuera de la ventana medida.

| Escenario | Éxitos | Error | Promedio | p95 | Máximo | CPU pico | Memoria pico | Resultado |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50 ventas | 50/50 | 0% | 227,34 ms | 253,85 ms | 256,88 ms | 24,4% | 75,44 MB | Cumple |
| 100 ventas | 100/100 | 0% | 907,36 ms | 996,88 ms | 1.005,15 ms | 19,8% | 79,31 MB | Cumple |

El criterio automatizado es p95 menor a 2.000 ms. Los dos escenarios cumplieron.

## Regresión

`make regression` ejecuta cobertura con umbral obligatorio e integración aislada. La misma secuencia forma parte de GitHub Actions para cada push y pull request.

## Recomendaciones

- Repetir la regresión cuando se conecte el nuevo frontend.
- Ejecutar y observar los workflows n8n cuando se complete esa fase.
- Repetir la carga sobre Oracle antes de usarlo como persistencia integrada.
- Añadir una prueba sostenida de al menos cinco minutos antes de producción.
