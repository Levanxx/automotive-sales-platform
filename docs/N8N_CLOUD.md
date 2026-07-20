# Guía de instalación y demostración en n8n Cloud

## 1. Componentes entregados

La carpeta `n8n/` contiene cuatro workflows importables:

1. **Seguimiento de prospectos inactivos:** consulta oportunidades sin avance, prepara una alerta por prospecto y la registra en AutoPulse.
2. **Sincronización comercial:** consulta prospectos, ventas, seguros, conversión por vendedor e indicadores; después registra un resumen consolidado.
3. **Monitor de salud:** comprueba los cuatro microservicios cada cinco minutos y registra una alerta si alguno falla.
4. **Manejador global de errores:** recibe los errores de los otros workflows y conserva workflow, ejecución y mensaje del fallo.

Los archivos no contienen claves reales, direcciones locales ni variables `$env`. Funcionan en planes Cloud que no ofrecen variables personalizadas.

## 2. Requisitos previos

- Los cuatro microservicios deben tener URLs públicas HTTPS.
- Los servicios de prospectos y dashboard deben compartir el mismo valor `N8N_AUTOMATION_KEY`.
- Deben existir datos de demostración. `python scripts/seed.py` crea un prospecto con cinco días de inactividad.
- n8n Cloud debe poder alcanzar las URLs públicas sin VPN ni direcciones `localhost`.

Ejemplo de configuración del backend:

```text
N8N_AUTOMATION_KEY=<valor largo y aleatorio>
```

La clave no debe guardarse dentro de Git ni escribirse directamente en los JSON.

## 3. Comprobación del backend antes de importar

Configure localmente las siguientes variables apuntando al backend publicado:

```text
N8N_PROSPECTS_URL=https://prospectos.example.com
N8N_SALES_URL=https://ventas.example.com
N8N_INSURANCE_URL=https://seguros.example.com
N8N_DASHBOARD_URL=https://dashboard.example.com
N8N_AUTOMATION_KEY=<la misma clave del backend>
```

Después ejecute:

```bash
python scripts/n8n_cloud_smoke_check.py
```

La comprobación valida salud, autenticación, consulta de inactividad, métricas y escritura/lectura de alertas. No continúe con n8n Cloud mientras alguna comprobación falle.

Antes del despliegue también puede comprobar toda la integración en un entorno local temporal con `make n8n-smoke`.

## 4. Crear la credencial en n8n Cloud

En **Credentials**, cree una credencial **Header Auth**:

| Campo | Valor |
|---|---|
| Credential name | `AutoPulse API Key` |
| Header name | `X-Automation-Key` |
| Header value | El valor de `N8N_AUTOMATION_KEY` |

Use la misma credencial en todos los nodos **HTTP Request**. Los archivos contienen una referencia ficticia `REEMPLAZAR_CREDENCIAL`; después de importar, n8n mostrará que debe seleccionarse una credencial real.

## 5. Importar y configurar

Importe desde **Import from File** en este orden:

1. `workflow-error-handler.json`
2. `inactive-prospect-alert.json`
3. `service-sync.json`
4. `service-health-monitor.json`

Después de cada importación:

1. Asigne la credencial **AutoPulse API Key** a cada nodo HTTP.
2. Sustituya las URLs `https://REEMPLAZAR-...example.com` en el nodo de configuración.
3. En el manejador de errores, cambie `dashboard_url` dentro de **Preparar detalle del error**.
4. Guarde el workflow sin publicarlo todavía.

En los ajustes de los tres workflows programados, seleccione **AutoPulse Cloud - Manejador global de errores** como *Error workflow*.

## 6. Pruebas manuales obligatorias

### Seguimiento de inactivos

1. Confirme que se ejecutó `scripts/seed.py` sobre la base utilizada.
2. Ejecute **Prueba manual**.
3. Verifique que **Obtener prospectos inactivos** encuentre al menos un registro.
4. Compruebe que **Registrar alerta en AutoPulse** responda `201`.
5. Consulte `GET /api/alerts` usando `X-Automation-Key` y confirme el evento `inactive_prospect`.

### Sincronización comercial

1. Ejecute **Prueba manual**.
2. Compruebe que todos los nodos HTTP terminen en verde.
3. Verifique el evento `service_sync` en `GET /api/alerts`.
4. Revise que el payload contenga cantidades, métricas y conversión por vendedor.

### Monitor de salud

1. Ejecute **Prueba manual** con las URLs correctas: los cuatro servicios deben indicar `ok`.
2. Cambie temporalmente una URL por una dirección inválida.
3. Ejecute nuevamente y confirme que se registra `service_health_failure`.
4. Restaure la URL correcta antes de publicar.

### Manejador de errores

1. Asigne el manejador como *Error workflow* de la sincronización.
2. Cambie temporalmente una URL de la sincronización por una inválida.
3. Publique temporalmente la sincronización con una frecuencia corta y espere una ejecución automática fallida.
4. Confirme el evento `n8n_workflow_error`, incluyendo nombre del workflow, ID de ejecución y mensaje.
5. Restaure la URL y frecuencia originales.

## 7. Publicación

Cuando todas las pruebas pasen:

1. Publique el manejador de errores.
2. Publique seguimiento de inactivos.
3. Publique sincronización comercial.
4. Publique el monitor de salud.
5. Confirme en **Executions** que las siguientes ejecuciones automáticas terminan correctamente.

## 8. Evidencias para la entrega

Guarde las siguientes capturas:

- Los cuatro workflows completos en el lienzo.
- Una ejecución exitosa de seguimiento de inactivos.
- Una ejecución exitosa de sincronización.
- Una ejecución saludable y una falla controlada del monitor.
- Una ejecución del manejador global de errores.
- La respuesta de `GET /api/alerts` con eventos `inactive_prospect`, `service_sync`, `service_health_failure` y `n8n_workflow_error`.
- La lista de workflows publicados y sus frecuencias.

No incluya en las capturas el valor de `N8N_AUTOMATION_KEY`.

## 9. Lista final de aceptación

- [ ] Backend público con HTTPS.
- [ ] Comprobación `n8n_cloud_smoke_check.py` aprobada.
- [ ] Cuatro JSON importados sin errores.
- [ ] URLs públicas sustituidas.
- [ ] Credencial asignada a todos los nodos HTTP.
- [ ] Manejador global asociado a los tres workflows programados.
- [ ] Cuatro pruebas manuales aprobadas.
- [ ] Workflows publicados.
- [ ] Evidencias guardadas sin secretos.
