# Documentación del endpoint de registro

## Endpoint
- URL: `POST /api/registro`
- Host: `http://37.187.27.45:8007`

## Propósito
Recibe los datos del formulario de registro de consumidor enviado desde el mapa y los guarda en un fichero de log.

## Payload JSON
El cuerpo de la petición debe enviarse en formato JSON con los siguientes campos:

```json
{
  "nombre": "Juan Pérez",
  "email": "juan.perez@example.com",
  "cups": "ES1234567890123456JA1A",
  "id_comunidad": "COM123",
  "aceptar_terminos": true
}
```

### Campos
- `nombre`: string
- `email`: string
- `cups`: string
- `id_comunidad`: string
- `aceptar_terminos`: boolean

## Respuesta esperada
```json
{
  "status": "success",
  "message": "Registro guardado correctamente"
}
```

## Notas
- No se realiza validación de datos; se guarda tal cual llega.

## Ejemplo de llamada `curl`
```bash
curl -X POST http://37.187.27.45:8007/api/registro \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "email": "juan.perez@example.com",
    "cups": "ES1234567890123456JA1A",
    "id_comunidad": "COM123",
    "aceptar_terminos": true
  }'
```

