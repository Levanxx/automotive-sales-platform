# Guía rápida de demostración

## Preparación

```bash
docker compose up --build -d
docker compose exec dashboard python scripts/seed.py
```

Abra `http://localhost:8004`.

## Recorrido sugerido

1. Muestre el resumen ejecutivo y explique los cinco indicadores.
2. Registre un prospecto desde **Prospectos**.
3. Avance la oportunidad por las etapas del embudo.
4. Registre el cierre desde **Ventas**.
5. Vincule una póliza desde **Seguros**.
6. Abra **Rendimiento** y presente los resultados de 50 y 100 ventas.

## Verificación técnica

```bash
python3 -m unittest discover -s tests -v
python3 scripts/integration_check.py
python3 load-tests/sales_load.py --concurrency 100
```

Para detener el entorno use `docker compose down`.
