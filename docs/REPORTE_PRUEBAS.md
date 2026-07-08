# Reporte final de pruebas

## Estrategia

La suite cubre validación, ciclo de prospectos, venta efectiva/fallida, unicidad de pólizas, métricas y conversión. CI exige cobertura de ramas de al menos 80%. Las pruebas de integración ejercitan los módulos sobre una base temporal con claves foráneas.

## Carga

`load-tests/sales_load.py` crea prospecto y venta por usuario virtual, con 50 o 100 operaciones concurrentes. Reporta promedio, p95, máximo, errores, duración y cumplimiento de p95 menor a 2 segundos. Al terminar publica el resultado en el dashboard de rendimiento.

## Resultados verificados — 7 de julio de 2026

| Escenario | Éxitos | Error | Promedio | p95 | Máximo | Resultado |
|---|---:|---:|---:|---:|---:|---|
| 50 ventas simultáneas | 50/50 | 0% | 56,64 ms | 86,41 ms | 91,31 ms | Cumple |
| 100 ventas simultáneas | 100/100 | 0% | 56,98 ms | 96,18 ms | 99,56 ms | Cumple |

La preparación de prospectos se ejecuta fuera de la ventana medida. La medición corresponde exclusivamente al registro concurrente de ventas. Los datos temporales se eliminan al terminar y los resultados permanecen en el dashboard de rendimiento.

## Recomendaciones

- Ejecutar una prueba de 5 minutos además del pulso concurrente antes de producción.
- Sustituir el volumen SQLite por Oracle en el entorno integrado y repetir la carga.
- Configurar alertas n8n con correo/Teams y credenciales fuera de los workflows.
- Observar CPU, memoria, conexiones y consultas lentas durante la prueba.
