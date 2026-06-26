# Prompt de estado y ejecución

## Resumen del software actual
- `app.py` inicializa FastAPI y carga las rutas desde `routes.py`.
- `routes.py` define todos los endpoints HTTP disponibles.
- `services.py` contiene la lógica de negocio y orquesta llamadas a:
  - `consulta_baisca_v30.py` para DATADIS
  - `pca_profiles.py` para PCA y clustering
- `consulta_baisca_v30.py` incluye `procesar_consumos()` y `generar_y_guardar_reading_register()`.
- `pca_profiles.py` implementa reducción PCA, reconstrucción y clustering k-means.

## Dependencias principales
- `fastapi`
- `uvicorn`
- `scikit-learn`
- `joblib`
- `pytest`
- `httpx`

## Estructura de archivos relevante
- `app.py`
- `routes.py`
- `services.py`
- `consulta_baisca_v30.py`
- `pca_profiles.py`
- `tests/`
- `logs/`
- `responses/`
- `registers/`

## Cómo arrancar el servidor
Desde la raíz del proyecto:

```bash
cd /home/oscar/Dropbox/22_IoE/_01_i+D/circulink/sw/api_mapa
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8007
```

> Para desarrollo local con recarga automática, añade `--reload`.

## Verificar el servidor
- Swagger: `http://localhost:8007/docs`
- ReDoc: `http://localhost:8007/redoc`

> Si usas el servidor público, reemplaza `localhost` por la dirección y puerto reales.

## Endpoints disponibles
- `POST /api/registro` — guarda registro de formulario.
- `GET /reading_register/{linea}` — genera el `reading_register` de DATADIS.
- `GET /ejecutar` — ejecuta `procesar_consumos()` y procesa consumos DATADIS.
- `POST /perfiles/pca_365x7` — reduce perfiles diarios 24h con PCA y guarda modelos.
- `POST /perfiles/pca/reconstruir` — reconstruye perfiles originales desde un fichero PCA reducido.
- `POST /perfiles/pca/kmeans` — clusteriza matrices PCA reducidas con k-means.

## Registro de formulario
`POST /api/registro` recibe:
- `nombre`
- `email`
- `cups`
- `id_comunidad`
- `aceptar_terminos`

Los datos se guardan en `logs/registros.log` con timestamp e información completa.

## Endpoints DATADIS
### `GET /reading_register/{linea}`
Genera `registers/reading_register.txt` a partir de una línea simplificada.

Formato esperado:

```
CUPS,CIF,distributorCode,pointType,year_ultima,month_ultima,year_final,month_final
```

Ejemplo:

```
ES0021000011297631SM,09404423E,8,5,2025,10,2025,10
```

### `GET /ejecutar`
Llama a `procesar_consumos()` en `consulta_baisca_v30.py`, lee `registers/reading_register.txt` y descarga los consumos de DATADIS.

Las respuestas se guardan en `responses/` con nombres del tipo:

```
ES0021000011464812SE_2025_01_2025_12.json
```

## Endpoints PCA
### `POST /perfiles/pca_365x7`
Reduce perfiles diarios de 24 horas usando `StandardScaler` + `PCA`.

Body JSON opcional:

```json
{
  "directorio": "responses",
  "output_directory": "responses/responses_pca",
  "models_directory": "responses/models",
  "n_components": 12,
  "file_pattern": "*.json"
}
```

- `directorio` por defecto: `responses`
- `output_directory` por defecto: `responses/responses_pca`
- `models_directory` por defecto: `responses/models`
- `n_components` por defecto: `7`
- `file_pattern` por defecto: `*.json`

El endpoint:
- lee los JSON de `responses/`
- genera perfiles diarios 24h
- ajusta PCA según `n_components`
- guarda ficheros reducidos en `responses/responses_pca/`
- crea un `model_id` único
- serializa PCA y StandardScaler en `responses/models/<model_id>/models.joblib`
- guarda metadata en `responses/models/<model_id>/metadata.json`
- actualiza el índice global `responses/models/index.json`

### Estructura de salida PCA
```
responses/
├── responses_pca/                      # Perfiles reducidos
│   └── *_pca<N>.json                   # Incluye model_id para reconstrucción
└── models/                             # Modelos serializados y metadata
    ├── index.json                      # Índice global de modelos
    └── pca_YYYYMMDD_HHMMSS_<hash>/    # Modelo único
        ├── models.joblib
        └── metadata.json
```

### `POST /perfiles/pca/kmeans`
Clusteriza los ficheros PCA reducidos.

Body JSON opcional:

```json
{
  "directorio": "responses/responses_pca",
  "output_directory": "responses/responses_pca/kmean1",
  "n_clusters": 24,
  "file_pattern": "*_pca*.json",
  "random_state": 42
}
```

- lee ficheros PCA reducidos en `responses/responses_pca/`
- ejecuta k-means
- guarda resultados en `responses/responses_pca/kmean1/`
- devuelve centroides, asignaciones y clusters

### `POST /perfiles/pca/caracterizacion`
Caracteriza cada cluster kmeans según la distribución de fechas y tipos de día.

Body JSON opcional:

```json
{
  "directorio": "responses/responses_pca/kmean1",
  "output_directory": "responses/responses_pca/kmean1",
  "file_pattern": "*_kmeans*.json",
  "holiday_file": "holidays.json"
}
```

- lee ficheros kmeans (`*_kmeans*.json`) en `directorio`.
- calcula para cada cluster la distribución de meses, estaciones, días laborables y festivos.
- guarda los resultados en `output_directory` con sufijo `_characterization.json`.
- devuelve la caracterización por cluster para su uso en asignación probabilística.

### `POST /perfiles/pca/centroides`
Reconstruye el consumo horario (24 h) a partir de los centroides ya calculados.

Body JSON opcional:

```json
{
  "directorio": "responses/responses_pca/kmean1",
  "output_directory": "responses/responses_pca/kmean1",
  "file_pattern": "*_kmeans*.json",
  "centroides_subdir": "centroides1"
}
```

- `directorio` por defecto: `responses/responses_pca/kmean1` (donde aparecen las respuestas kmeans).
- `output_directory` por defecto: `responses/responses_pca/kmean1`.

- `centroides_subdir` por defecto: `centroides1`. Es el nombre del subdirectorio dentro de `output_directory` donde se
  guardarán los ficheros resultantes de los centroides reconstruidos. Puedes cambiarlo para mantener distintas
  ejecuciones separadas (p.ej. `centroides_experimentoA`).

Comportamiento:
- Lee ficheros kmeans (`*_kmeans*.json`) en `directorio`.
- Para cada fichero obtiene los `cluster_centroids` y el `model_id` asociado.
- Carga el modelo PCA + `StandardScaler` desde `responses/models/<model_id>/` y aplica
  `pca.inverse_transform()` + `scaler.inverse_transform()` sobre cada centroide para obtener
  el consumo reconstruido de 24 horas.
- Guarda dos ficheros por ejecución en `output_directory/centroides1/`:
  1) `*_centroides_components.json` — centroides en espacio de componentes.
  2) `*_centroides_24h.json` — centroides reconstruidos a consumo horario (24 valores por centroide).

Si quieres usar otro nombre de carpeta para los centroides, envía `centroides_subdir` en el body. Por ejemplo:

```bash
curl -s -X POST http://localhost:8007/perfiles/pca/centroides \
  -H "Content-Type: application/json" \
  -d '{"directorio":"responses/responses_pca/kmean1","output_directory":"responses/responses_pca/kmean1","file_pattern":"*_kmeans*.json","centroides_subdir":"centroides_experimentoA"}' | jq
```

Los ficheros resultantes se guardarán en `responses/responses_pca/kmean1/centroides_experimentoA/`.

Notas:
- El `model_id` debe existir en `responses/models/` y contener los PCA y scalers serializados.
- Si falta el modelo para un `model_id`, la ejecución incluirá el error en el resumen y continuará.

### `POST /perfiles/pca/reconstruir`
Reconstruye perfiles originales desde un fichero PCA reducido.

Body JSON:

```json
{
  "output_file": "ES0021000011464812SE_2025_01_2025_12_pca12.json",
  "models_directory": "responses/models"
}
```

- busca el fichero en la ruta absoluta o en `responses/responses_pca/`
- extrae `model_id` del JSON PCA reducido
- carga el modelo correspondiente desde `responses/models/<model_id>/`
- reconstruye los valores originales
- guarda el resultado en `responses/rebuilt/`

> Nota: El alias antiguo `/perfiles/pca_365x7/reconstruir` no está expuesto actualmente en el código.

## Uso desde el formulario
Ejemplo de envío a `POST /api/registro`:

```javascript
const datos = {
  nombre: "Juan",
  email: "juan@example.com",
  cups: "ES1234567890123456JA1A",
  id_comunidad: "COM123",
  aceptar_terminos: true
};

fetch('http://localhost:8007/api/registro', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(datos)
})
.then(r => r.json())
.then(data => console.log(data));
```

## Notas importantes
- El registro del formulario se guarda en `logs/registros.log`.
- `GET /reading_register/{linea}` genera `registers/reading_register.txt`.
- `GET /ejecutar` usa ese registro para descargar consumos DATADIS.
- El número real de componentes PCA en el fichero de salida se refleja en el nombre `_pca<N>.json`.

## Pruebas con Pytest
- `pytest` está en `requirements.txt`.
- Añadir o actualizar pruebas en `tests/test_services.py` y `tests/test_routes.py`.
- Para endpoints FastAPI, usar `fastapi.testclient.TestClient` y `monkeypatch`.
- Ejecutar desde la raíz del proyecto:

```bash
pytest
```

## Configuración Git local
- Se utiliza Git con VS Code.
- Asegúrate de no subir archivos temporales ni resultados de ejecución.
- Configuración global sugerida:
  - `git config --global user.name "onsar"`
  - `git config --global user.email "oscar.puyal@gmail.com"`
