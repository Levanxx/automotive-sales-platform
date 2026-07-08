# Reporte final de pruebas

## Estrategia

La suite cubre validación, ciclo de prospectos, venta efectiva/fallida, unicidad de pólizas, métricas y conversión. CI exige cobertura de ramas de al menos 80%. Las pruebas de integración ejercitan los módulos sobre una base temporal con claves foráneas.

## Carga

`load-tests/sales_load.py` crea prospecto y venta por usuario virtual, con 50 o 100 operaciones concurrentes. Reporta promedio, p95, máximo, errores, duración y cumplimiento de p95 menor a 2 segundos.

Los resultados dependen del equipo y deben capturarse en el entorno de entrega. No se inventan cifras: ejecute ambos escenarios con los contenedores activos y adjunte las salidas. Criterios: tasa de error 0% y p95 menor a 2.000 ms para 100 operaciones.

## Recomendaciones

- Ejecutar una prueba de 5 minutos además del pulso concurrente antes de producción.
- Sustituir el volumen SQLite por Oracle en el entorno integrado y repetir la carga.
- Configurar alertas n8n con correo/Teams y credenciales fuera de los workflows.
- Observar CPU, memoria, conexiones y consultas lentas durante la prueba.

