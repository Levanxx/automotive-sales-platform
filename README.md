# AutoPulse — gestión de prospectos y ventas

Proyecto final ejecutable para una empresa automotriz: embudo comercial, ventas efectivas/fallidas, seguros, dashboard, automatización n8n y pruebas de carga.

## Arranque

```bash
docker compose up --build -d
docker compose exec dashboard python scripts/seed.py
```

Abra `http://localhost:8004`. La consola web permite gestionar prospectos, ventas, seguros, KPI y rendimiento. Salud de servicios: puertos 8001–8004, ruta `/health`.

## Calidad

```bash
python -m unittest discover -s tests -v
coverage run --branch -m unittest discover -s tests && coverage report --fail-under=80
python scripts/integration_check.py
python load-tests/sales_load.py --concurrency 50
python load-tests/sales_load.py --concurrency 100
```

## Entregables

- `services/`: cuatro microservicios y frontend responsive.
- `database/oracle/`: DDL y DML Oracle 23ai Free.
- `n8n/`: seguimiento de inactivos y sincronización de métricas.
- `tests/` y `load-tests/`: pruebas funcionales, integración y estrés.
- `docs/`: manual, despliegue, arquitectura y reporte de pruebas.

Ejemplos listos para copiar: [docs/API_EJEMPLOS.md](docs/API_EJEMPLOS.md).

## Documentación de entrega

- [Resumen de entrega](docs/ENTREGA_FINAL.md)
- [Matriz de aceptación](docs/MATRIZ_ACEPTACION.md)
- [Guía de demostración](docs/GUIA_DEMOSTRACION.md)

Consulte [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md) para Oracle y n8n.
