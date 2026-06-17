import logging
from datetime import datetime
import json
from pathlib import Path

# Importar funciones de DATADIS desde el directorio raíz de api_mapa
try:
    from consulta_baisca_v30 import procesar_consumos, generar_y_guardar_reading_register
except ImportError:
    # Fallback si los módulos no están disponibles
    procesar_consumos = None
    generar_y_guardar_reading_register = None

try:
    from pca_profiles import reducir_perfiles_diarios_pca, reconstruir_perfiles_desde_salida_pca
except ImportError:
    reducir_perfiles_diarios_pca = None
    reconstruir_perfiles_desde_salida_pca = None

# Configurar logging a fichero
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "registros.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def guardar_registro(datos: dict) -> None:
    """
    Guarda los datos del formulario en el log sin validar.
    """
    try:
        logger.info(f"Registro recibido: {json.dumps(datos, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"Error al guardar registro: {str(e)}")
        raise


def generar_reading_register_service(linea: str) -> dict:
    """
    Servicio para configurar la consulta a DATADIS.
    
    Parámetros:
        linea (str): Línea de configuración DATADIS.
                    Ejemplo: ES0021000009999999VV,14444448L,8,5,2025,1,2025,12
    
    Retorna:
        dict: Resultado de la operación
    """
    try:
        if generar_y_guardar_reading_register is None:
            return {"status": "error", "detail": "Módulo datadis no disponible"}
        
        resultado = generar_y_guardar_reading_register(linea)
        return resultado
    
    except Exception as e:
        logger.error(f"Error en generar_reading_register_service: {str(e)}")
        return {"status": "error", "detail": str(e)}


def ejecutar_consulta_datadis_service() -> dict:
    """
    Servicio para consultar a DATADIS y procesar consumos.
    
    Retorna:
        dict: Resultado de la operación
    """
    try:
        if procesar_consumos is None:
            return {"status": "error", "detail": "Módulo datadis no disponible"}
        
        procesar_consumos()
        return {
            "status": "ok",
            "message": "Procesamiento de consumos completado exitosamente"
        }
    
    except Exception as e:
        logger.error(f"Error en ejecutar_consulta_datadis_service: {str(e)}")
        return {"status": "error", "detail": str(e)}


def reducir_perfiles_diarios_pca_service(directorio: str = "responses", output_directory: str = "responses/responses_pca", n_components: int = 7, file_pattern: str = "*.json", models_directory: str = "responses/models") -> dict:
    """
    Servicio que aplica PCA a perfiles diarios 24h cargados desde ficheros JSON.
    Guarda los modelos PCA y scaler en models_directory con metadata y model_id.
    """
    try:
        if reducir_perfiles_diarios_pca is None:
            return {"status": "error", "detail": "La funcionalidad PCA no está disponible."}

        resultado = reducir_perfiles_diarios_pca(directorio, output_directory, n_components, file_pattern, models_directory)
        return resultado

    except ImportError as e:
        return {"status": "error", "detail": str(e)}
    except Exception as e:
        logger.error(f"Error en reducir_perfiles_diarios_pca_service: {str(e)}")
        return {"status": "error", "detail": str(e)}


def reconstruir_perfiles_pca_service(output_file: str, models_directory: str = "responses/models") -> dict:
    """
    Servicio para reconstruir perfiles de 24h a partir de un fichero *_pca7.json
    y un modelo PCA guardado.
    """
    try:
        if reconstruir_perfiles_desde_salida_pca is None:
            return {"status": "error", "detail": "La funcionalidad de reconstrucción PCA no está disponible."}

        resultado = reconstruir_perfiles_desde_salida_pca(output_file, models_directory)
        return resultado

    except ImportError as e:
        return {"status": "error", "detail": str(e)}
    except Exception as e:
        logger.error(f"Error en reconstruir_perfiles_pca_service: {str(e)}")
        return {"status": "error", "detail": str(e)}
