# Matriz de criterios de aceptación

| Criterio | Evidencia | Estado |
|---|---|---|
| Gestionar prospectos y etapas | Consola web y servicio de prospectos | Cumple |
| Registrar ventas realizadas y fallidas | Servicio y módulo web de ventas | Cumple |
| Vincular seguros a ventas efectivas | Servicio y módulo web de seguros | Cumple |
| Mostrar indicadores y embudo | Dashboard en tiempo real | Cumple |
| Cobertura mínima de 80% | Reporte de cobertura: 91% | Cumple |
| Integración de microservicios | Verificador `scripts/integration_check.py` | Cumple |
| Simulación de 50 ventas | p95 86,41 ms, error 0% | Cumple |
| Simulación de 100 ventas en menos de 2 s | p95 96,18 ms, error 0% | Cumple |
| Workflows n8n documentados | Archivos importables en `n8n/` | Cumple |
| Scripts Oracle 23ai | DDL y datos de prueba en `database/oracle/` | Cumple |
| Manual y despliegue | Documentación en `docs/` | Cumple |

Los valores de rendimiento corresponden a la ejecución verificada del 7 de julio de 2026 en el entorno local de entrega.
