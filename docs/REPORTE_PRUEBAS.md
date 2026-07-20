# Reporte final de pruebas de backend

## Alcance

La regresión cubre los microservicios de prospectos, ventas, seguros y métricas, la persistencia SQLite, la estructura de los scripts Oracle, los escenarios de carga y la estructura de los cuatro workflows n8n Cloud. El frontend y la ejecución dentro de la cuenta n8n Cloud quedan fuera de la regresión local.

## Pruebas unitarias y de contrato

La suite contiene 43 pruebas automatizadas. Todas aprobaron. La cobertura combinada de líneas y ramas es 85%, por encima del umbral obligatorio de 80%.

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
| 50 ventas | 50/50 | 0% | 226,13 ms | 241,64 ms | 244,09 ms | 9,3% | 76,03 MB | Cumple |
| 100 ventas | 100/100 | 0% | 531,45 ms | 615,37 ms | 624,44 ms | 24,5% | 79,80 MB | Cumple |

El criterio automatizado es p95 menor a 2.000 ms. Los dos escenarios cumplieron.

## n8n Cloud

`python scripts/validate_n8n.py` comprueba que estén presentes los cuatro workflows, que sus conexiones apunten a nodos existentes, que tengan triggers y zona horaria, que se importen inactivos y que no contengan URLs internas, `$env` ni credenciales reales.

`python scripts/n8n_cloud_smoke_check.py` valida el backend público antes de importar: salud, autenticación, inactividad, métricas y almacenamiento de alertas. La prueba final dentro de n8n Cloud requiere completar la lista de evidencias de `docs/N8N_CLOUD.md`.

## Regresión

`make regression` ejecuta cobertura con umbral obligatorio, integración aislada y validación de workflows n8n. La misma secuencia forma parte de GitHub Actions para cada push y pull request.

## Recomendaciones

- Repetir la regresión cuando se conecte el nuevo frontend.
- Completar la lista de evidencias después de importar y publicar los workflows en n8n Cloud.
- Repetir la carga sobre Oracle antes de usarlo como persistencia integrada.
- Añadir una prueba sostenida de al menos cinco minutos antes de producción.
