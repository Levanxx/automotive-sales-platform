# Arquitectura

Cuatro procesos HTTP independientes separan prospectos, ventas, seguros y dashboard. Para que el proyecto sea ejecutable en un portátil, comparten un volumen SQLite con transacciones WAL; se incluyen scripts equivalentes de Oracle 23ai Free. n8n consume las APIs internas y el dashboard sirve tanto métricas agregadas como la interfaz.

| Servicio | Puerto | Responsabilidad |
|---|---:|---|
| Prospectos | 8001 | Contactos, etapas e inactividad |
| Ventas | 8002 | Cierres, pérdidas y conversión |
| Seguros | 8003 | Pólizas prospectadas/vendidas |
| Dashboard | 8004 | KPI, embudo e interfaz web |

Para producción se recomienda una base Oracle única inicialmente, autenticación OIDC, API gateway, secretos administrados, observabilidad OpenTelemetry y separación física de esquemas por servicio.

