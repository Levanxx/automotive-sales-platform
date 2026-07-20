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

Copie `.env.example` como `.env`, configure `ALERT_WEBHOOK_URL` para Teams, Slack u otro receptor HTTP e inicie con `docker compose --profile automation up n8n`. Abra `http://localhost:5678`, importe los dos JSON de `n8n/` y active los flujos. Las URLs internas ya apuntan a los servicios Compose.

## Verificación

```bash
python scripts/seed.py
python -m unittest discover -s tests -v
python scripts/integration_check.py --self-contained
python scripts/stress_check.py
make regression
```

`stress_check.py` levanta servicios y una base temporal, ejecuta 50 y 100 ventas, mide latencia, errores, CPU y memoria, y elimina el entorno al finalizar. Las pruebas contra un entorno ya iniciado publican automáticamente sus resultados mediante `/api/performance`.
