import glob
import json
import os
from datetime import datetime
from pathlib import Path
import hashlib
import platform
import sys

try:
    import joblib
except ImportError:
    joblib = None


def _generate_model_id() -> str:
    """Genera un model_id único basado en timestamp y hash."""
    from datetime import datetime as dt
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    hash_val = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"pca_{timestamp}_{hash_val}"


def _parse_time_value(time_str: str) -> int:
    try:
        return int(time_str.split(':')[0])
    except Exception:
        return 0


def _load_daily_profiles(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    days = {}
    for record in records:
        date_key = record.get('date')
        time_key = record.get('time')
        value = record.get('consumptionKWh')

        if date_key is None or time_key is None or value is None:
            continue

        days.setdefault(date_key, []).append((time_key, value))

    daily_profiles = []
    for date_key, values in sorted(days.items(), key=lambda x: datetime.strptime(x[0], '%Y/%m/%d')):
        values_sorted = sorted(values, key=lambda item: _parse_time_value(item[0]))
        profile = [float(v) for _, v in values_sorted]
        if len(profile) == 24:
            daily_profiles.append((date_key, profile))

    return daily_profiles


def reducir_perfiles_diarios_pca(
    directorio='responses',
    output_directory='responses/responses_pca',
    n_components=7,
    file_pattern='*.json',
    models_directory='responses/models'
):
    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        raise ImportError('scikit-learn es requerido para PCA. Instala scikit-learn en requirements.txt.') from e

    if not os.path.isdir(directorio):
        return {
            'status': 'error',
            'message': f'Directorio no encontrado: {directorio}'
        }

    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(models_directory, exist_ok=True)
    
    file_paths = sorted(glob.glob(os.path.join(directorio, file_pattern)))

    if not file_paths:
        return {
            'status': 'error',
            'message': f'No se encontraron ficheros en {directorio} con patrón {file_pattern}'
        }

    outputs = []
    processed = 0
    model_id = _generate_model_id()
    all_pca_models = []
    all_scalers = []
    file_sources = []

    for file_path in file_paths:
        daily_profiles = _load_daily_profiles(file_path)
        if not daily_profiles:
            continue

        dates = [item[0] for item in daily_profiles]
        matrix = [item[1] for item in daily_profiles]

        if len(matrix) < 2:
            continue

        scaler = StandardScaler()
        scaled = scaler.fit_transform(matrix)

        pca = PCA(n_components=min(n_components, min(len(matrix), len(matrix[0]))))
        reduced = pca.fit_transform(scaled)

        output_rows = []
        for date_key, reduced_values in zip(dates, reduced):
            output_rows.append({
                'date': date_key,
                'components': [float(v) for v in reduced_values],
                'model_id': model_id
            })

        output_filename = os.path.basename(file_path).replace('.json', f'_pca{pca.n_components_}.json')
        output_path = os.path.join(output_directory, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'input_file': os.path.basename(file_path),
                'model_id': model_id,
                'n_days': len(dates),
                'n_components': pca.n_components_,
                'explained_variance_ratio': [float(v) for v in pca.explained_variance_ratio_],
                'profiles': output_rows
            }, f, indent=2, ensure_ascii=False)

        outputs.append({
            'input_file': os.path.basename(file_path),
            'output_file': output_path,
            'n_days': len(dates),
            'n_components': pca.n_components_,
            'explained_variance_ratio': [float(v) for v in pca.explained_variance_ratio_]
        })
        processed += 1
        all_pca_models.append(pca)
        all_scalers.append(scaler)
        file_sources.append(os.path.basename(file_path))

    if processed == 0:
        return {
            'status': 'error',
            'message': 'No se procesaron ficheros válidos. Comprueba que tienen 24 horas por día.'
        }

    # Serializar y guardar modelos y metadata
    model_save_result = _save_models_and_metadata(
        model_id=model_id,
        pca_models=all_pca_models,
        scalers=all_scalers,
        file_sources=file_sources,
        n_components=n_components,
        output_explained_variance=outputs[0]['explained_variance_ratio'] if outputs else None,
        models_directory=models_directory
    )

    return {
        'status': 'ok',
        'model_id': model_id,
        'processed_files': processed,
        'outputs': outputs,
        'output_directory': output_directory,
        'models_directory': models_directory,
        'model_save_result': model_save_result
    }


def _save_models_and_metadata(model_id, pca_models, scalers, file_sources, n_components, output_explained_variance, models_directory):
    """Guarda los modelos PCA y scaler junto con metadata."""
    from datetime import datetime as dt
    import pkg_resources
    
    try:
        sklearn_version = pkg_resources.get_distribution("scikit-learn").version
    except:
        sklearn_version = "unknown"
    
    # Crear directorio específico para el modelo
    model_dir = os.path.join(models_directory, model_id)
    os.makedirs(model_dir, exist_ok=True)
    
    # Guardar modelos usando joblib si está disponible, si no usar pickle
    try:
        if joblib:
            # Guardar todos los modelos en una estructura común
            model_data = {
                'pca_models': pca_models,
                'scalers': scalers,
                'n_models': len(pca_models),
                'model_id': model_id
            }
            joblib.dump(model_data, os.path.join(model_dir, 'models.joblib'), compress=3)
            save_method = 'joblib'
        else:
            import pickle
            model_data = {
                'pca_models': pca_models,
                'scalers': scalers,
                'n_models': len(pca_models),
                'model_id': model_id
            }
            with open(os.path.join(model_dir, 'models.pkl'), 'wb') as f:
                pickle.dump(model_data, f)
            save_method = 'pickle'
    except Exception as e:
        return {
            'status': 'error',
            'detail': f'Error guardando modelos: {str(e)}',
            'save_method': None
        }
    
    # Crear metadata JSON
    metadata = {
        'model_id': model_id,
        'created_at': dt.now().isoformat(),
        'created_by': 'pca_reduction_endpoint',
        'training_data': {
            'source_files': file_sources,
            'num_files': len(file_sources)
        },
        'pca_config': {
            'n_components': n_components,
            'n_models': len(pca_models),
            'explained_variance_ratio': output_explained_variance if output_explained_variance else []
        },
        'sklearn_version': sklearn_version,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': platform.platform(),
        'save_method': save_method,
        'model_files': {
            'models': 'models.joblib' if joblib else 'models.pkl'
        },
        'notes': 'Modelos PCA y StandardScaler usados para reducción 365x24 -> 365x7'
    }
    
    metadata_path = os.path.join(model_dir, 'metadata.json')
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return {
            'status': 'error',
            'detail': f'Error guardando metadata: {str(e)}'
        }
    
    # Guardar también un índice global de modelos
    _update_models_index(models_directory, model_id, metadata)
    
    return {
        'status': 'ok',
        'model_id': model_id,
        'model_directory': model_dir,
        'metadata_file': metadata_path,
        'save_method': save_method
    }


def _load_model_data(model_dir):
    """Carga los datos serializados de PCA y scalers desde disco."""
    model_path_joblib = os.path.join(model_dir, 'models.joblib')
    model_path_pickle = os.path.join(model_dir, 'models.pkl')

    if os.path.exists(model_path_joblib) and joblib:
        return joblib.load(model_path_joblib)
    if os.path.exists(model_path_pickle):
        import pickle
        with open(model_path_pickle, 'rb') as f:
            return pickle.load(f)

    raise FileNotFoundError(f"No se encontró ningún archivo de modelo en {model_dir}")


def _load_pca_reduced_profiles(file_path):
    """Carga un fichero PCA reducido y devuelve fechas, matriz de componentes y metadatos."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    profiles = data.get('profiles', [])
    if not profiles:
        raise ValueError('El fichero PCA no contiene perfiles válidos.')

    dates = []
    matrix = []
    n_components = None
    for row in profiles:
        date = row.get('date')
        components = row.get('components')
        if date is None or components is None:
            continue
        if n_components is None:
            n_components = len(components)
        elif len(components) != n_components:
            raise ValueError('Inconsistencia en el número de componentes del fichero PCA.')
        dates.append(date)
        matrix.append([float(v) for v in components])

    if not dates:
        raise ValueError('No se encontraron fechas válidas en el fichero PCA.')

    return dates, matrix, n_components, data.get('input_file'), data.get('model_id')


def cluster_pca_profiles_kmeans(
    directorio='responses/responses_pca',
    output_directory=None,
    n_clusters=24,
    file_pattern='*_pca*.json',
    random_state=42
):
    try:
        from sklearn.cluster import KMeans
    except ImportError as e:
        raise ImportError('scikit-learn es requerido para k-means. Instala scikit-learn en requirements.txt.') from e

    if output_directory is None:
        output_directory = os.path.join(directorio, 'kmeans_results')

    if not os.path.isdir(directorio):
        return {
            'status': 'error',
            'message': f'Directorio no encontrado: {directorio}'
        }

    os.makedirs(output_directory, exist_ok=True)
    file_paths = sorted(glob.glob(os.path.join(directorio, file_pattern)))

    if not file_paths:
        return {
            'status': 'error',
            'message': f'No se encontraron ficheros en {directorio} con patrón {file_pattern}'
        }

    outputs = []
    processed = 0

    for file_path in file_paths:
        try:
            dates, matrix, n_components, input_file, model_id = _load_pca_reduced_profiles(file_path)
        except Exception as e:
            continue

        if len(matrix) < 2:
            continue

        if n_clusters <= 0:
            return {
                'status': 'error',
                'message': 'El número de centroides debe ser mayor que 0.'
            }

        if n_clusters > len(matrix):
            return {
                'status': 'error',
                'message': f'El número de centroides ({n_clusters}) no puede ser mayor que el número de días ({len(matrix)}).'
            }

        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init='auto')
        labels = kmeans.fit_predict(matrix)
        centroids = kmeans.cluster_centers_.tolist()

        assignments = [
            {'date': dates[i], 'cluster': int(labels[i]), 'day_index': i}
            for i in range(len(dates))
        ]

        clusters = {}
        for idx, label in enumerate(labels):
            clusters.setdefault(int(label), []).append(dates[idx])

        clusters_summary = [
            {
                'cluster': cluster_id,
                'count': len(dates_list),
                'dates': dates_list
            }
            for cluster_id, dates_list in sorted(clusters.items())
        ]

        output_filename = os.path.basename(file_path).replace('.json', f'_kmeans{n_clusters}.json')
        output_path = os.path.join(output_directory, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'input_file': input_file,
                'source_pca_file': os.path.basename(file_path),
                'model_id': model_id,
                'n_days': len(dates),
                'n_components': n_components,
                'n_clusters': n_clusters,
                'cluster_centroids': centroids,
                'assignments': assignments,
                'clusters': clusters_summary
            }, f, indent=2, ensure_ascii=False)

        outputs.append({
            'input_file': input_file,
            'source_pca_file': os.path.basename(file_path),
            'output_file': output_path,
            'n_days': len(dates),
            'n_components': n_components,
            'n_clusters': n_clusters,
            'model_id': model_id
        })
        processed += 1

    if processed == 0:
        return {
            'status': 'error',
            'message': 'No se procesaron ficheros PCA válidos. Comprueba que el directorio contiene matrices reducidas.'
        }

    return {
        'status': 'ok',
        'processed_files': processed,
        'outputs': outputs,
        'output_directory': output_directory,
        'input_directory': directorio,
        'n_clusters': n_clusters,
        'random_state': random_state
    }


def reconstruir_centroides_desde_kmeans(
    directorio='responses/responses_pca/kmean1',
    output_directory=None,
    file_pattern='*_kmeans*.json',
    models_directory='responses/models'
):
    """Reconstruye consumos horarios (24h) a partir de los centroides de ficheros kmeans.

    Guarda dos ficheros por ejecución en un subdirectorio `centroides1` bajo
    `output_directory` (por defecto `directorio`):
      - *_centroides_components.json  (centroides en espacio de componentes)
      - *_centroides_24h.json        (centroides reconstruidos a 24 valores)
    """
    try:
        import numpy as np
    except Exception:
        np = None

    if output_directory is None:
        output_directory = directorio

    centroides_dir = os.path.join(output_directory, 'centroides1')
    os.makedirs(centroides_dir, exist_ok=True)

    if not os.path.isdir(directorio):
        return {'status': 'error', 'message': f'Directorio no encontrado: {directorio}'}

    file_paths = sorted(glob.glob(os.path.join(directorio, file_pattern)))
    if not file_paths:
        return {'status': 'error', 'message': f'No se encontraron ficheros en {directorio} con patrón {file_pattern}'}

    outputs = []
    processed = 0

    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            outputs.append({'file': file_path, 'status': 'error', 'detail': str(e)})
            continue

        source_pca_file = data.get('input_file') or data.get('source_pca_file')
        model_id = data.get('model_id')
        centroids = data.get('cluster_centroids') or data.get('cluster_centroids_') or []

        if not centroids:
            outputs.append({'file': file_path, 'status': 'error', 'detail': 'No se encontraron centroides en el fichero kmeans'})
            continue

        # Preparar salida de componentes
        basename = os.path.basename(file_path).replace('.json', '')
        components_path = os.path.join(centroides_dir, f"{basename}_centroides_components.json")
        with open(components_path, 'w', encoding='utf-8') as f:
            json.dump({'source_kmeans_file': os.path.basename(file_path), 'cluster_centroids': centroids}, f, indent=2, ensure_ascii=False)

        # Intentar reconstruir cada centroide a 24h usando el modelo serializado
        rebuilt_list = []
        try:
            model_dir = os.path.join(models_directory, model_id) if model_id else None
            if not model_dir or not os.path.isdir(model_dir):
                raise FileNotFoundError(f'Modelo no encontrado: {model_dir}')

            # Cargar metadata para localizar el índice del fichero fuente
            metadata_path = os.path.join(model_dir, 'metadata.json')
            if not os.path.isfile(metadata_path):
                raise FileNotFoundError(f'Metadata no encontrada en {model_dir}')

            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            training_files = metadata.get('training_data', {}).get('source_files', [])
            if source_pca_file not in training_files:
                raise ValueError(f'El fichero fuente {source_pca_file} no está registrado en metadata del modelo')

            index = training_files.index(source_pca_file)
            model_data = _load_model_data(model_dir)
            pca_models = model_data.get('pca_models', [])
            scalers = model_data.get('scalers', [])

            if index >= len(pca_models) or index >= len(scalers):
                raise IndexError('No se encontró PCA o scaler correspondiente en el modelo para el fichero fuente')

            pca = pca_models[index]
            scaler = scalers[index]

            for i, centroid in enumerate(centroids):
                try:
                    comps = np.array(centroid).reshape(1, -1) if np is not None else None
                    reconstructed_scaled = pca.inverse_transform(comps)
                    reconstructed = scaler.inverse_transform(reconstructed_scaled)
                    reconstructed_values = [float(v) for v in reconstructed.flatten()]
                    rebuilt_list.append({'cluster': int(i), 'reconstructed_24h': reconstructed_values})
                except Exception as e:
                    rebuilt_list.append({'cluster': int(i), 'error': str(e)})

            # Guardar fichero reconstruido
            recon_path = os.path.join(centroides_dir, f"{basename}_centroides_24h.json")
            with open(recon_path, 'w', encoding='utf-8') as f:
                json.dump({'source_kmeans_file': os.path.basename(file_path), 'model_id': model_id, 'reconstructed_centroids': rebuilt_list}, f, indent=2, ensure_ascii=False)

            outputs.append({'file': file_path, 'status': 'ok', 'components_file': components_path, 'reconstructed_file': recon_path})
            processed += 1

        except Exception as e:
            outputs.append({'file': file_path, 'status': 'error', 'detail': str(e)})
            continue

    if processed == 0:
        return {'status': 'error', 'message': 'No se procesaron ficheros kmeans válidos.', 'outputs': outputs}

    return {'status': 'ok', 'processed_files': processed, 'outputs': outputs, 'output_directory': centroides_dir}


def _resolve_output_file_path(output_file_path):
    """Resuelve el path del fichero PCA de salida a partir de un nombre o ruta."""
    if os.path.isabs(output_file_path) and os.path.exists(output_file_path):
        return output_file_path

    normalized = os.path.normpath(output_file_path)
    if os.path.exists(normalized):
        return normalized

    default_path = os.path.join('responses', 'responses_pca', os.path.basename(output_file_path))
    if os.path.exists(default_path):
        return default_path

    return normalized


def reconstruir_perfiles_desde_salida_pca(output_file_path, models_directory='responses/models', rebuilt_directory='responses/rebuilt'):
    """Reconstruye los perfiles originales de 24h desde un fichero PCA y el modelo guardado.
    Guarda el resultado reconstruido en `responses/rebuilt/` usando el mismo nombre de fichero de entrada.
    """
    output_file_path = _resolve_output_file_path(output_file_path)

    if not os.path.isfile(output_file_path):
        return {
            'status': 'error',
            'message': f'Fichero de salida PCA no encontrado: {output_file_path}'
        }

    with open(output_file_path, 'r', encoding='utf-8') as f:
        output_data = json.load(f)

    model_id = output_data.get('model_id')
    input_file = output_data.get('input_file')
    profiles = output_data.get('profiles', [])
    explained_variance_ratio = output_data.get('explained_variance_ratio')

    if not model_id or not input_file or not profiles:
        return {
            'status': 'error',
            'message': 'El fichero de salida PCA no contiene la información necesaria (model_id, input_file o profiles).'
        }

    model_dir = os.path.join(models_directory, model_id)
    metadata_path = os.path.join(model_dir, 'metadata.json')
    if not os.path.isfile(metadata_path):
        return {
            'status': 'error',
            'message': f'Metadata del modelo no encontrada: {metadata_path}'
        }

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    training_files = metadata.get('training_data', {}).get('source_files', [])
    if input_file not in training_files:
        return {
            'status': 'error',
            'message': f'El archivo de salida PCA no coincide con ningún fichero fuente registrado en el modelo: {input_file}'
        }

    index = training_files.index(input_file)
    model_data = _load_model_data(model_dir)
    pca_models = model_data.get('pca_models', [])
    scalers = model_data.get('scalers', [])

    if index >= len(pca_models) or index >= len(scalers):
        return {
            'status': 'error',
            'message': 'No se encontró el modelo PCA o scaler correspondiente para el fichero de salida.'
        }

    pca = pca_models[index]
    scaler = scalers[index]

    components = [row.get('components', []) for row in profiles]
    dates = [row.get('date') for row in profiles]

    if not components or any(len(c) == 0 for c in components):
        return {
            'status': 'error',
            'message': 'No se encontraron componentes válidas en el fichero de salida PCA.'
        }

    try:
        reconstructed_scaled = pca.inverse_transform(components)
        reconstructed = scaler.inverse_transform(reconstructed_scaled)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error al reconstruir los datos: {str(e)}'
        }

    reconstructed_profiles = []
    for date, values in zip(dates, reconstructed):
        reconstructed_profiles.append({
            'date': date,
            'reconstructed_values': [float(v) for v in values]
        })

    os.makedirs(rebuilt_directory, exist_ok=True)
    rebuilt_filename = os.path.basename(output_file_path)
    rebuilt_path = os.path.join(rebuilt_directory, rebuilt_filename)
    rebuilt_data = {
        'model_id': model_id,
        'input_file': input_file,
        'source_pca_file': output_file_path,
        'n_days': len(reconstructed_profiles),
        'n_components': len(components[0]),
        'explained_variance_ratio': explained_variance_ratio,
        'reconstructed_profiles': reconstructed_profiles
    }
    with open(rebuilt_path, 'w', encoding='utf-8') as f:
        json.dump(rebuilt_data, f, indent=2, ensure_ascii=False)

    return {
        'status': 'ok',
        'model_id': model_id,
        'input_file': input_file,
        'n_days': len(reconstructed_profiles),
        'n_components': len(components[0]),
        'explained_variance_ratio': explained_variance_ratio,
        'rebuilt_file': rebuilt_path
    }


def _update_models_index(models_directory, model_id, metadata):
    """Actualiza el índice global de modelos disponibles."""
    index_path = os.path.join(models_directory, 'index.json')
    
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except:
            index = {'models': []}
    else:
        index = {'models': []}
    
    # Añadir o actualizar entrada del modelo
    existing = next((m for m in index['models'] if m['model_id'] == model_id), None)
    if not existing:
        index['models'].append({
            'model_id': model_id,
            'created_at': metadata['created_at'],
            'path': os.path.join(model_id, 'metadata.json'),
            'status': 'active'
        })
    
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Advertencia: No se pudo actualizar índice de modelos: {str(e)}")

