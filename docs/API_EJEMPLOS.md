# Ejemplos de API

## Crear prospecto

```bash
curl -X POST http://localhost:8001/prospects -H 'Content-Type: application/json' -d '{"name":"María López","email":"maria@email.pe","phone":"999111222","vehicle_interest":"Toyota Corolla","seller_id":1}'
```

## Avanzar a negociación

```bash
curl -X PATCH http://localhost:8001/prospects/1 -H 'Content-Type: application/json' -d '{"stage":"negotiation"}'
```

## Cerrar venta

```bash
curl -X POST http://localhost:8002/sales -H 'Content-Type: application/json' -d '{"prospect_id":1,"vehicle_id":1,"seller_id":1,"amount":24990,"status":"completed"}'
```

## Vincular seguro

```bash
curl -X POST http://localhost:8003/insurance -H 'Content-Type: application/json' -d '{"sale_id":1,"type":"Todo riesgo","expected_premium":1250,"actual_premium":1190,"status":"sold"}'
```

## Conversión por vendedor y por etapa

```bash
curl http://localhost:8002/sales/conversion
curl http://localhost:8002/sales/conversion/stages
```
