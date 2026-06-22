# Prompt de estado y ejecución

## Qué se ha hecho
- Se creó la estructura base con FastAPI en `app.py`.
- Se añadió `requirements.txt` con las dependencias necesarias:
  - `fastapi`
  - `uvicorn`
  - `scikit-learn`
  - `joblib`
- **Endpoint `POST /api/registro`**:
  - recibe datos del formulario `FormularioRegistro.jsx`
  - Campos: nombre, email, cups, id_comunidad, aceptar_terminos
  - Guarda en `logs/registros.log` sin validar
- **Endpoints DATADIS**:
  - `GET /reading_register/{linea}` - Configurar la consulta a DATADIS
  - `GET /ejecutar` - Ejecutar `procesar_consumos()` y procesar consumos DATADIS
- **Endpoints PCA**:
  - `POST /perfiles/pca_365x7` - Reduce los perfiles diarios 24h a un número parametrizable de componentes mediante `StandardScaler` + `PCA`
  - `POST /perfiles/pca/reconstruir` - Reconstruye perfiles originales desde salida PCA
  - `POST /perfiles/pca/kmeans` - Clusteriza matrices PCA reducidas usando k-means
  - Lee los ficheros JSON de `responses/`
  - Genera salidas en `responses/responses_pca/`
  - Guarda los objetos PCA y StandardScaler en `responses/models/` con `model_id`
- Lógica de negocio actualizada en:
  - `routes.py` (endpoints)
  - `services.py` (servicios)
  - `pca_profiles.py` (lógica PCA)

## Cambio de estructura
- `app.py`: inicia FastAPI y carga el router desde `routes.py`
- `routes.py`: define todos los endpoints HTTP
- `services.py`: contiene la lógica de negocio, servicios DATADIS y servicio PCA
- `consulta_baisca_v30.py`: contiene `procesar_consumos()` y `generar_y_guardar_reading_register()`
- `pca_profiles.py`: contiene la lógica de reducción PCA de perfiles diarios

## Cómo arrancar el servidor
### En el servidor accesible desde internet
```bash
cd /home/oscar/sw/envs
source datadis_api/bin/activate
cd /home/oscar/sw/mapas
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8007
```

> Si quieres desarrollo con recarga automática solo en el servidor de prueba, añade `--reload`, pero en un servidor público no es recomendable.

## Verificar el servidor
Una vez iniciado, puedes acceder a la documentación interactiva de Swagger en:

```
http://37.187.27.45:8007/docs
```

O a ReDoc en:

```
http://37.187.27.45:8007/redoc
```

## Endpoints disponibles
- `POST /api/registro` - guardar registro de formulario
- `GET /reading_register/{linea}` - generar `reading_register` para DATADIS
- `GET /ejecutar` - ejecutar la consulta a DATADIS y procesar consumos
- `POST /perfiles/pca_365x7` - reducir perfiles diarios 24h a un número parametrizable de componentes usando PCA, guardar modelos en `responses/models/` con trazabilidad `model_id`
- `POST /perfiles/pca/reconstruir` - reconstruir la matriz original 365x24 desde un fichero PCA generado y el modelo existente
- `POST /perfiles/pca/kmeans` - clusterizar matrices PCA reducidas (365×7) usando k-means, generar centroides y asignaciones de días

## Uso del endpoint PCA
POST a `http://37.187.27.45:8007/perfiles/pca_365x7` con un body JSON opcional:

```json
{
  "directorio": "responses",
  "output_directory": "responses/responses_pca",
  "models_directory": "responses/models",
  "n_components": 12,
  "file_pattern": "*.json"
}
```

El endpoint acepta `n_components` para ajustar cuántas componentes usar; el valor por defecto es `7` si no se envía.

El endpoint:
- Lee todos los JSON de `responses/`, crea perfiles diarios de 24 horas y guarda ficheros reducidos en `responses/responses_pca/`.
- **Nuevo**: Genera un `model_id` único, serializa los objetos PCA y StandardScaler en `responses/models/<model_id>/`, guarda metadata en `responses/models/<model_id>/metadata.json`.
- Cada perfil reducido incluye el `model_id` en su JSON para trazabilidad y futura reconstrucción.
- Mantiene un índice global de modelos en `responses/models/index.json` para referencia rápida.

## Uso del endpoint de clustering PCA
POST a `http://37.187.27.45:8007/perfiles/pca/kmeans` con un body JSON opcional:

```json
{
  "directorio": "responses/responses_pca",
  "output_directory": "responses/responses_pca/kmean1",
  "n_clusters": 24,
  "file_pattern": "*_pca*.json",
  "random_state": 42
}
```

El endpoint:
- Lee las matrices PCA reducidas de `responses/responses_pca/` por defecto.
- Ejecuta `k-means` sobre cada fichero de perfiles `365×7`.
- Guarda el resultado en el subdirectorio `responses/responses_pca/kmean1/` por defecto.
- Devuelve centroides `k×7`, asignaciones de cada día al centroide y los días agrupados por cluster.

## Uso del endpoint de reconstrucción PCA
POST a `http://37.187.27.45:8007/perfiles/pca/reconstruir` con un body JSON:

```json
{
  "output_file": "ES0021000011464812SE_2025_01_2025_12_pca12.json",
  "models_directory": "responses/models"
}
```

El endpoint también soporta el alias antiguo `POST /perfiles/pca_365x7/reconstruir` y buscará el fichero bajo `responses/responses_pca/` si se indica sólo el nombre.

El endpoint devuelve:
- `model_id`
- `input_file`
- `n_days`
- `n_components`
- `explained_variance_ratio`
- `rebuilt_file` con la ruta del fichero guardado en `responses/rebuilt/`

El resultado reconstruido se guarda en fichero y no se devuelve en la respuesta para minimizar la carga JSON.

**Estructura de salida**:
```
responses/
├── responses_pca/                      # Perfiles reducidos (365x7)
│   └── *_pca7.json                     # Incluye model_id para reconstrucción
└── models/                             # Modelos serializados y metadata
    ├── index.json                      # Índice global de modelos
    └── pca_YYYYMMDD_HHMMSS_<hash>/
        ├── models.joblib               # Modelos PCA + scalers serializados
        └── metadata.json               # Metadata del modelo
```

## Usar el endpoint desde el formulario
El formulario debe hacer un POST a `http://37.187.27.45:8007/api/registro` con:

```javascript
const datos = {
  nombre: "Juan",
  email: "juan@example.com",
  cups: "ES1234567890123456JA1A",
  id_comunidad: "COM123",
  aceptar_terminos: true
};

fetch('http://37.187.27.45:8007/api/registro', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(datos)
})
.then(r => r.json())
.then(data => console.log(data));
```

Los registros se guardan en `logs/registros.log` con timestamp e información completa.

## Notas de actualización
- Este fichero sirve como guía de estado y ejecución.
- Si se añaden nuevas rutas o dependencias, actualizar este archivo con:
  1. nuevas rutas y su propósito
  2. nuevos paquetes en `requirements.txt`
  3. cambios en la forma de arrancar el servidor

## Pruebas con Pytest
- `pytest` ya está listado en `requirements.txt`.
- Añadir o actualizar pruebas en `tests/`, por ejemplo `tests/test_services.py` y `tests/test_routes.py`.
- Para endpoints FastAPI, usar `fastapi.testclient.TestClient` y `monkeypatch` para simular dependencias externas.
- Ejecutar las pruebas desde el directorio raíz del proyecto con:

```bash
pytest
```
- Los resultados de ejecución se guardan en `logs/pytest.log` y `logs/pytest_results.xml`.
- Documentar en el informe qué pruebas se añadieron y qué funcionalidades cubren.

## Configuración Git local
- El repositorio se integra con Git desde VS Code.
- Configuración global aplicada:
  - `git config --global user.name "onsar"`
  - `git config --global user.email "oscar.puyal@gmail.com"`
- Asegúrate de usar `.gitignore` para no subir archivos temporales, de configuración o resultados de ejecución.
  1. nuevas rutas y su propósito
  2. nuevos paquetes en `requirements.txt`
  3. cambios en la forma de arrancar el servidor

## Cambio reciente: Serialización y trazabilidad de modelos PCA (June 2026)
- El endpoint PCA ahora guarda los modelos PCA + StandardScaler en directorio `responses/models/` con estructura:
  - Cada modelo obtiene un `model_id` único generado automáticamente.
  - Los objetos se serializan con joblib en `responses/models/<model_id>/models.joblib`.
  - Se genera `responses/models/<model_id>/metadata.json` con información completa del modelo (versiones, parámetros, fecha creación).
  - Se mantiene `responses/models/index.json` como referencia global de todos los modelos.
- Cada perfil reducido incluye el `model_id` en su JSON para permitir reconstrucción posterior (365x7 → 365x24).
- Para reconstruir: carga el modelo desde `responses/models/<model_id>/models.joblib` y aplica `pca.inverse_transform()` + `scaler.inverse_transform()`.
- Requiere instalar: `joblib` (añadido a `requirements.txt`).

## Comentario
- Se ha añadido funcionalidad DATADIS sin necesidad de autenticación.
- Se ha añadido funcionalidad PCA para reducción de perfiles diarios.
- Se ha añadido persistencia y trazabilidad de modelos para garantizar reproducibilidad y reconstrucción posterior.
- Se recomienda validar que los ficheros `responses/` y `registers/` existen antes de ejecutar en producción.

## Cambios recientes (June 2026)
- **Endpoint eliminado**: `GET /` (read_root) se removió del servidor.
- **Directorio por defecto actualizado**: El endpoint `/perfiles/pca/kmeans` ahora usa `responses/responses_pca/kmean1/` como directorio de salida por defecto.
- **Alias eliminado**: `/perfiles/pca_365x7/reconstruir` fue eliminado; usar solo `/perfiles/pca/reconstruir`.
- **Pruebas actualizadas**: Se actualizaron los archivos de prueba en `tests/`:
  - `test_routes.py`: Eliminada la prueba `test_read_root()`, actualizada `test_cluster_pca_profiles_kmeans_route()` con el nuevo directorio por defecto, añadidas pruebas para `test_reducir_perfiles_pca_route()`, `test_reconstruir_perfiles_pca_route()` y `test_ejecutar_script_route()`.
  - `test_services.py`: Añadidas pruebas para `test_cluster_pca_profiles_kmeans_service_missing()` y `test_cluster_pca_profiles_kmeans_service_default_output_dir()` para verificar que el directorio por defecto es correcto.
  - `conftest.py`: Sin cambios, la configuración de logging sigue siendo válida.
