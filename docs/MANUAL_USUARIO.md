# Manual de usuario

## Panel comercial

Abra `http://localhost:8004`. El panel muestra prospectos activos, ventas realizadas y fallidas, tasa de conversión, seguros vinculados y el embudo. Se actualiza cada 15 segundos o con **Actualizar**.

La navegación lateral permite operar el sistema completo:

- **Prospectos:** registrar contactos, filtrar el embudo y avanzar etapas.
- **Ventas:** cerrar una oportunidad como realizada o fallida, con motivo de pérdida.
- **Seguros:** vincular una póliza a una venta efectiva y comparar primas.
- **Rendimiento:** consultar los resultados reales de las pruebas de 50 y 100 operaciones concurrentes.

## Operación del proceso

1. En **Prospectos**, pulse **Nuevo prospecto** y complete los datos.
2. Use **Avanzar** para moverlo por prospección, calificación, negociación y cierre.
3. En **Ventas**, pulse **Registrar venta** y seleccione el resultado. Las pérdidas requieren motivo.
4. En **Seguros**, vincule la póliza a una venta efectiva.
5. Revise el resumen y el embudo en **Resumen ejecutivo**.

Los errores se responden como JSON con el campo `error`. Un prospecto solo puede tener una venta y una venta solo puede tener un seguro.
