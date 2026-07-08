# Configuración y despliegue

## Requisitos

- Docker Desktop con Compose v2.
- Puertos 8001–8004 libres. n8n usa 5678 y Oracle 1521 cuando se activan sus perfiles.

## Inicio rápido

```bash
docker compose up --build
docker compose exec dashboard python scripts/seed.py
```

El panel queda en `http://localhost:8004`. La aplicación usa SQLite compartido para una demostración inmediata.

## Oracle 23ai Free

Inicie Oracle con `docker compose --profile oracle up oracle`. Espere el estado saludable y ejecute, en orden, `database/oracle/001_schema.sql` y `002_seed.sql` con SQLcl o SQL Developer. Los scripts DDL/DML incluyen integridad referencial e índices. La implementación de demostración usa SQLite; la capa de persistencia es el punto de sustitución para un driver Oracle.

## n8n

Inicie con `docker compose --profile automation up n8n`, abra `http://localhost:5678` e importe los dos JSON de `n8n/`. Revise credenciales/canales de alerta y active los flujos. Las URLs internas ya apuntan a los servicios Compose.

## Verificación

```bash
python scripts/seed.py
python -m unittest discover -s tests -v
python load-tests/sales_load.py --concurrency 50
python load-tests/sales_load.py --concurrency 100
```

