# Manual de usuario

## Panel comercial

Abra `http://localhost:8004`. El panel muestra prospectos activos, ventas realizadas y fallidas, tasa de conversión, seguros vinculados y el embudo. Se actualiza cada 15 segundos o con **Actualizar**.

## Operación del proceso

1. Registre un prospecto con `POST /prospects` en el puerto 8001.
2. Avance su etapa con `PATCH /prospects/{id}`: `initial`, `qualification`, `negotiation` o `closed`.
3. Registre el cierre con `POST /sales` en el puerto 8002. Use `completed` o `failed`; el último requiere `loss_reason`.
4. Para una venta efectiva, vincule la póliza con `POST /insurance` en el puerto 8003.
5. Consulte indicadores en `GET /api/metrics` del puerto 8004.

Los errores se responden como JSON con el campo `error`. Un prospecto solo puede tener una venta y una venta solo puede tener un seguro.

