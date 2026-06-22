from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import (
    guardar_registro,
    generar_reading_register_service,
    ejecutar_consulta_datadis_service,
    reducir_perfiles_diarios_pca_service,
    reconstruir_perfiles_pca_service,
    cluster_pca_profiles_kmeans_service,
)

router = APIRouter()

class RegistroConsumidor(BaseModel):
    nombre: str
    email: str
    cups: str
    id_comunidad: str
    aceptar_terminos: bool

@router.post("/api/registro")
async def registrar_consumidor(registro: RegistroConsumidor):
    try:
        guardar_registro(registro.dict())
        return {"status": "success", "message": "Registro guardado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reading_register/{linea}", summary="Configurar la consulta a DATADIS")
def generar_reading_register(linea: str):
    """
    Configura la consulta a DATADIS para una línea específica.
    
    Parámetros:
        linea (str): Formato ejemplo: ES0021000009999999VV,14444448L,8,5,2025,1,2025,12
    """
    try:
        resultado = generar_reading_register_service(linea)
        return resultado
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/ejecutar", summary="Consultar a DATADIS")
def ejecutar_script():
    """
    Consulta a DATADIS y procesa los consumos.
    """
    try:
        resultado = ejecutar_consulta_datadis_service()
        return resultado
    except Exception as e:
        return {"status": "error", "detail": str(e)}


class SolicitudPCA(BaseModel):
    directorio: str = "responses"
    output_directory: str = "responses/responses_pca"
    models_directory: str = "responses/models"
    n_components: int = 7
    file_pattern: str = "*.json"


class SolicitudReconstruccionPCA(BaseModel):
    output_file: str
    models_directory: str = "responses/models"


class SolicitudKMeansPCA(BaseModel):
    directorio: str = "responses/responses_pca"
    output_directory: str = "responses/responses_pca/kmean1"
    n_clusters: int = 24
    file_pattern: str = "*_pca*.json"
    random_state: int = 42


@router.post("/perfiles/pca_365x7", summary="Reducir perfiles diarios con PCA usando un número parametrizable de componentes")
def reducir_perfiles_diarios_pca(solicitud: SolicitudPCA):
    """
    Aplica StandardScaler + PCA a perfiles diarios de 24h en JSON.
    Guarda los modelos PCA y scaler en directorio models/ con metadata y model_id para trazabilidad.
    """
    try:
        resultado = reducir_perfiles_diarios_pca_service(
            solicitud.directorio,
            solicitud.output_directory,
            solicitud.n_components,
            solicitud.file_pattern,
            solicitud.models_directory
        )
        return resultado
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/perfiles/pca/reconstruir", summary="Reconstruir perfiles originales desde salida PCA")
def reconstruir_perfiles_diarios_pca(solicitud: SolicitudReconstruccionPCA):
    """
    Reconstruye los perfiles originales de 24h a partir de un fichero *_pca7.json
    y del modelo PCA+scaler existente.
    """
    try:
        resultado = reconstruir_perfiles_pca_service(
            solicitud.output_file,
            solicitud.models_directory
        )
        return resultado
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/perfiles/pca/kmeans", summary="Clusterizar perfiles PCA usando k-means")
def cluster_pca_profiles_kmeans(solicitud: SolicitudKMeansPCA):
    """
    Aplica k-means sobre los perfiles PCA reducidos (365x7) y genera centroides, asignaciones de días y clusters.
    """
    try:
        resultado = cluster_pca_profiles_kmeans_service(
            solicitud.directorio,
            solicitud.output_directory,
            solicitud.n_clusters,
            solicitud.file_pattern,
            solicitud.random_state,
        )
        return resultado
    except Exception as e:
        return {"status": "error", "detail": str(e)}
