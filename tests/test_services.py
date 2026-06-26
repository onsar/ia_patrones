import json
import os

import pytest

from pca_profiles import cluster_pca_profiles_kmeans
from services import (
    guardar_registro,
    generar_reading_register_service,
    ejecutar_consulta_datadis_service,
    reducir_perfiles_diarios_pca_service,
    reconstruir_perfiles_pca_service,
    cluster_pca_profiles_kmeans_service,
    caracterizar_clusters_kmeans_service,
)


def test_guardar_registro_no_error(monkeypatch):
    monkeypatch.setattr("services.logger.info", lambda msg: None)
    guardar_registro({"nombre": "Usuario", "email": "user@example.com", "cups": "ES0021000009999999VV"})


def test_generar_reading_register_service_module_missing(monkeypatch):
    monkeypatch.setattr("services.generar_y_guardar_reading_register", None)
    resultado = generar_reading_register_service("ES0021000009999999VV,14444448L,8,5,2025,1,2025,12")
    assert resultado == {"status": "error", "detail": "Módulo datadis no disponible"}


def test_generar_reading_register_service_exception(monkeypatch):
    def fake(linea):
        raise ValueError("fallo de prueba")

    monkeypatch.setattr("services.generar_y_guardar_reading_register", fake)
    resultado = generar_reading_register_service("linea")
    assert resultado["status"] == "error"
    assert "fallo de prueba" in resultado["detail"]


def test_ejecutar_consulta_datadis_service_module_missing(monkeypatch):
    monkeypatch.setattr("services.procesar_consumos", None)
    resultado = ejecutar_consulta_datadis_service()
    assert resultado == {"status": "error", "detail": "Módulo datadis no disponible"}


def test_ejecutar_consulta_datadis_service_success(monkeypatch):
    called = {"ok": False}

    def fake():
        called["ok"] = True

    monkeypatch.setattr("services.procesar_consumos", fake)
    resultado = ejecutar_consulta_datadis_service()
    assert resultado["status"] == "ok"
    assert called["ok"] is True


def test_reducir_perfiles_diarios_pca_service_missing(monkeypatch):
    monkeypatch.setattr("services.reducir_perfiles_diarios_pca", None)
    resultado = reducir_perfiles_diarios_pca_service()
    assert resultado == {"status": "error", "detail": "La funcionalidad PCA no está disponible."}


def test_reconstruir_perfiles_pca_service_missing(monkeypatch):
    monkeypatch.setattr("services.reconstruir_perfiles_desde_salida_pca", None)
    resultado = reconstruir_perfiles_pca_service("responses/sample_pca7.json")
    assert resultado == {"status": "error", "detail": "La funcionalidad de reconstrucción PCA no está disponible."}


def test_cluster_pca_profiles_kmeans_service_missing(monkeypatch):
    monkeypatch.setattr("services.cluster_pca_profiles_kmeans", None)
    resultado = cluster_pca_profiles_kmeans_service()
    assert resultado == {"status": "error", "detail": "La funcionalidad de clustering PCA no está disponible."}


def test_cluster_pca_profiles_kmeans_service_default_output_dir(monkeypatch):
    """Verifica que el directorio por defecto es responses/responses_pca/kmean1"""
    called_args = {}
    
    def fake_kmeans(*args, **kwargs):
        called_args["directorio"] = args[0] if args else None
        called_args["output_directory"] = args[1] if len(args) > 1 else None
        return {"status": "ok", "processed_files": 0, "outputs": []}
    
    monkeypatch.setattr("services.cluster_pca_profiles_kmeans", fake_kmeans)
    resultado = cluster_pca_profiles_kmeans_service()
    
    assert resultado["status"] == "ok"
    assert called_args["directorio"] == "responses/responses_pca"
    assert called_args["output_directory"] == "responses/responses_pca/kmean1"


def test_cluster_pca_profiles_kmeans(tmp_path):
    sample_file = tmp_path / "sample_pca.json"
    sample_data = {
        "input_file": "source.json",
        "model_id": "test-model",
        "n_days": 5,
        "n_components": 7,
        "profiles": [
            {"date": f"2025/01/{i+1:02d}", "components": [float(i + j) for j in range(7)]}
            for i in range(5)
        ]
    }
    sample_file.write_text(json.dumps(sample_data), encoding='utf-8')

    output_dir = tmp_path / "kmeans_results"
    resultado = cluster_pca_profiles_kmeans(
        directorio=str(tmp_path),
        output_directory=str(output_dir),
        n_clusters=2,
        file_pattern="*.json",
        random_state=0
    )

    assert resultado["status"] == "ok"
    assert resultado["processed_files"] == 1
    assert os.path.isdir(str(output_dir))
    assert len(resultado["outputs"]) == 1

    output_path = resultado["outputs"][0]["output_file"]
    assert os.path.exists(output_path)

    with open(output_path, 'r', encoding='utf-8') as f:
        loaded = json.load(f)

    assert loaded["n_clusters"] == 2
    assert len(loaded["cluster_centroids"]) == 2
    assert len(loaded["assignments"]) == 5
    assert all("date" in item and "cluster" in item for item in loaded["assignments"])


def test_caracterizar_clusters_kmeans_service_missing(monkeypatch):
    monkeypatch.setattr("services.caracterizar_clusters_kmeans", None)
    resultado = caracterizar_clusters_kmeans_service()
    assert resultado == {"status": "error", "detail": "La funcionalidad de caracterización de clusters no está disponible."}


def test_caracterizar_clusters_kmeans_service(tmp_path):
    kmean_dir = tmp_path / "responses" / "responses_pca" / "kmean1"
    kmean_dir.mkdir(parents=True)

    sample_data = {
        "input_file": "source.json",
        "model_id": "test-model",
        "assignments": [
            {"date": "2025/01/01", "cluster": 0},
            {"date": "2025/01/02", "cluster": 0},
            {"date": "2025/07/01", "cluster": 1},
            {"date": "2025/07/05", "cluster": 1}
        ]
    }

    sample_file = kmean_dir / "sample_kmeans24.json"
    sample_file.write_text(json.dumps(sample_data), encoding='utf-8')

    resultado = caracterizar_clusters_kmeans_service(
        directorio=str(kmean_dir),
        output_directory=str(kmean_dir),
        file_pattern="*.json"
    )

    assert resultado["status"] == "ok"
    assert len(resultado["outputs"]) == 1

    output_path = resultado["outputs"][0]["output_file"]
    assert os.path.exists(output_path)

    with open(output_path, 'r', encoding='utf-8') as f:
        loaded = json.load(f)

    assert loaded["n_clusters"] == 2
    assert len(loaded["cluster_characterization"]) == 2
    assert any(cluster["cluster_id"] == 0 for cluster in loaded["cluster_characterization"])
    assert any(cluster["cluster_id"] == 1 for cluster in loaded["cluster_characterization"])
