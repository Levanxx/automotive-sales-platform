# Matriz de criterios de aceptación

| Criterio | Evidencia | Estado |
|---|---|---|
| Gestionar prospectos y etapas | API de prospectos, validación secuencial e historial de etapas | Cumple |
| Registrar ventas realizadas y fallidas | Servicio y módulo web de ventas | Cumple |
| Vincular seguros a ventas efectivas | Servicio y módulo web de seguros | Cumple |
| Mostrar indicadores y embudo | Dashboard en tiempo real | Cumple |
| Cobertura mínima de 80% | 46 pruebas, cobertura combinada de líneas y ramas: 89% | Cumple |
| Integración de microservicios | Recorrido HTTP aislado con `scripts/integration_check.py --self-contained` | Cumple |
| Simulación de 50 ventas | 50/50, p95 241,64 ms, error 0% | Cumple |
| Simulación de 100 ventas en menos de 2 s | 100/100, p95 615,37 ms, error 0% | Cumple |
| Uso de recursos en carga | CPU pico y memoria pico incluidos en el reporte | Cumple |
| Workflows n8n preparados | Cuatro JSON Cloud, autenticación, reintentos, errores y validador automático | Cumple |
| Workflows n8n ejecutándose | Requiere importación, URLs públicas y capturas de ejecución Cloud | Pendiente de evidencia Cloud |
| Scripts Oracle 23ai | DDL completo, DML y validación estructural automatizada | Cumple |
| Manual y despliegue | Documentación en `docs/` | Cumple |

Los valores de rendimiento corresponden a la ejecución aislada verificada del 19 de julio de 2026. La regresión valida los JSON n8n, pero la evidencia de ejecución en n8n Cloud se completa después de importarlos.
