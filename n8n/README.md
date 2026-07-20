# Workflows AutoPulse para n8n Cloud

| Archivo | Propósito | Frecuencia |
|---|---|---|
| `inactive-prospect-alert.json` | Detecta prospectos sin avance y registra una alerta por prospecto | Cada 24 horas |
| `service-sync.json` | Consolida prospectos, ventas, seguros, conversión y métricas | Cada 15 minutos |
| `service-health-monitor.json` | Comprueba la disponibilidad de los cuatro microservicios | Cada 5 minutos |
| `workflow-error-handler.json` | Registra los errores no controlados de los otros workflows | Al ocurrir un error |

Todos se importan inactivos, usan la zona horaria `America/Lima`, reintentan llamadas HTTP y requieren asignar la credencial **AutoPulse API Key** después de importarlos.

La instalación y las pruebas están documentadas en [`docs/N8N_CLOUD.md`](../docs/N8N_CLOUD.md). Antes de entregar, ejecute:

```bash
python scripts/validate_n8n.py
```
