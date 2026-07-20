# Entrega final

AutoPulse implementa el ciclo comercial automotriz desde el registro del prospecto hasta el cierre de la venta y la vinculación de seguros.

## Componentes entregados

- Consola web responsive para prospectos, ventas, seguros e indicadores.
- Cuatro microservicios independientes desplegables con Docker Compose.
- Persistencia local de demostración y scripts DDL/DML para Oracle 23ai Free.
- Cuatro automatizaciones n8n Cloud para inactividad, sincronización, salud y errores.
- Pruebas unitarias, de integración y de carga.
- Documentación de usuario, arquitectura, API y despliegue.

## Resultados verificados

- 46 pruebas automatizadas aprobadas.
- 89% de cobertura combinada de líneas y ramas.
- Integración HTTP completa entre los cuatro microservicios aprobada.
- 50 ventas simultáneas: p95 de 241,64 ms y 0% de errores.
- 100 ventas simultáneas: p95 de 615,37 ms y 0% de errores.

Los resultados corresponden a la regresión de backend del 19 de julio de 2026. Se entregan cuatro workflows validados estructuralmente para n8n Cloud, autenticación separada y una guía de demostración. La ejecución Cloud debe completarse después de configurar las URLs públicas; las pruebas del frontend conectado se mantienen fuera de esta fase.

El panel principal está disponible en `http://localhost:8004` después de iniciar los contenedores.
