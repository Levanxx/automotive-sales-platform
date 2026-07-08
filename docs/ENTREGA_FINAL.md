# Entrega final

AutoPulse implementa el ciclo comercial automotriz desde el registro del prospecto hasta el cierre de la venta y la vinculación de seguros.

## Componentes entregados

- Consola web responsive para prospectos, ventas, seguros e indicadores.
- Cuatro microservicios independientes desplegables con Docker Compose.
- Persistencia local de demostración y scripts DDL/DML para Oracle 23ai Free.
- Automatizaciones n8n para inactividad y sincronización.
- Pruebas unitarias, de integración y de carga.
- Documentación de usuario, arquitectura, API y despliegue.

## Resultados verificados

- 17 pruebas automatizadas aprobadas.
- 91% de cobertura de código.
- 50 ventas simultáneas: p95 de 86,41 ms y 0% de errores.
- 100 ventas simultáneas: p95 de 96,18 ms y 0% de errores.

El panel principal está disponible en `http://localhost:8004` después de iniciar los contenedores.
