# Procedimiento de pruebas con Pytest

1. Añadir las pruebas al proyecto
   - Crear o actualizar archivos bajo `tests/`, por ejemplo `tests/test_services.py` y `tests/test_routes.py`.
   - Cada prueba debe cubrir una función o ruta importante y casos clave: éxito, errores, entradas faltantes o dependencias no disponibles.

2. Simular dependencias externas
   - Usar `monkeypatch` para sustituir funciones externas o módulos no disponibles.
   - Esto asegura que las pruebas sean deterministas y no dependan de servicios externos.

3. Ejecutar Pytest localmente
   - Instalar dependencias en el entorno actual antes de ejecutar las pruebas:

```bash
python -m pip install -r requirements.txt
```

   - Desde el directorio raíz del proyecto ejecutar `pytest`.
   - Revisar resultados y corregir fallos de inmediato.

4. Añadir cobertura al incluir nuevo código
   - Para cada nueva función/servicio, escribir al menos una prueba de comportamiento normal y una de manejo de errores.
   - Para nuevos endpoints de FastAPI, usar `fastapi.testclient.TestClient`.

5. Actualizar dependencias
   - Incluir `pytest` en `requirements.txt` si aún no está presente.

6. Documentar cambios
   - Registrar en el informe qué pruebas se añadieron y qué funcionalidades cubren.

Este procedimiento mantiene el proyecto robusto y ayuda a validar rápidamente el código nuevo antes de integrarlo.