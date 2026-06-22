import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app import app


def test_registrar_consumidor(monkeypatch):
    monkeypatch.setattr("routes.guardar_registro", lambda datos: None)
    client = TestClient(app)

    payload = {
        "nombre": "Usuario",
        "email": "user@example.com",
        "cups": "ES0021000009999999VV",
        "id_comunidad": "1234",
        "aceptar_terminos": True,
    }

    response = client.post("/api/registro", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Registro guardado correctamente"}


def test_generar_reading_register_route_when_module_missing(monkeypatch):
    monkeypatch.setattr("routes.generar_reading_register_service", lambda linea: {"status": "error", "detail": "Módulo datadis no disponible"})
    client = TestClient(app)
    response = client.get("/reading_register/test")
    assert response.status_code == 200
    assert response.json() == {"status": "error", "detail": "Módulo datadis no disponible"}


def test_ejecutar_script_route(monkeypatch):
    monkeypatch.setattr(
        "routes.ejecutar_consulta_datadis_service",
        lambda: {
            "status": "ok",
            "message": "Procesamiento de consumos completado exitosamente"
        }
    )
    client = TestClient(app)
    response = client.get("/ejecutar")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "Procesamiento" in response.json()["message"]


def test_cluster_pca_profiles_kmeans_route(monkeypatch):
    monkeypatch.setattr(
        "routes.cluster_pca_profiles_kmeans_service",
        lambda directorio, output_directory, n_clusters, file_pattern, random_state: {
            "status": "ok",
            "processed_files": 1,
            "output_directory": output_directory,
            "n_clusters": n_clusters,
            "input_directory": directorio,
            "outputs": [
                {
                    "input_file": "source.json",
                    "source_pca_file": "source_pca.json",
                    "output_file": f"{output_directory}/source_pca_kmeans{n_clusters}.json",
                    "n_days": 365,
                    "n_components": 7,
                    "n_clusters": n_clusters,
                    "model_id": "test-model"
                }
            ]
        }
    )
    client = TestClient(app)
    payload = {
        "directorio": "responses/responses_pca",
        "output_directory": "responses/responses_pca/kmean1",
        "n_clusters": 24,
        "file_pattern": "*_pca*.json",
        "random_state": 42,
    }

    response = client.post("/perfiles/pca/kmeans", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["n_clusters"] == 24
    assert response.json()["processed_files"] == 1


def test_reducir_perfiles_pca_route(monkeypatch):
    monkeypatch.setattr(
        "routes.reducir_perfiles_diarios_pca_service",
        lambda directorio, output_directory, n_components, file_pattern, models_directory: {
            "status": "ok",
            "model_id": "pca_20260622_120000_abc12345",
            "processed_files": 1,
            "outputs": [
                {
                    "input_file": "sample.json",
                    "output_file": "responses/responses_pca/sample_pca7.json",
                    "n_days": 365,
                    "n_components": 7,
                    "explained_variance_ratio": [0.5, 0.2, 0.1, 0.08, 0.05, 0.04, 0.03]
                }
            ]
        }
    )
    client = TestClient(app)
    payload = {
        "directorio": "responses",
        "output_directory": "responses/responses_pca",
        "models_directory": "responses/models",
        "n_components": 7,
        "file_pattern": "*.json"
    }

    response = client.post("/perfiles/pca_365x7", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "model_id" in response.json()
    assert response.json()["processed_files"] == 1


def test_reconstruir_perfiles_pca_route(monkeypatch):
    monkeypatch.setattr(
        "routes.reconstruir_perfiles_pca_service",
        lambda output_file, models_directory: {
            "status": "ok",
            "model_id": "pca_20260622_120000_abc12345",
            "input_file": "sample_pca7.json",
            "n_days": 365,
            "n_components": 7,
            "explained_variance_ratio": [0.5, 0.2, 0.1, 0.08, 0.05, 0.04, 0.03],
            "rebuilt_file": "responses/rebuilt/sample_rebuilt.json"
        }
    )
    client = TestClient(app)
    payload = {
        "output_file": "sample_pca7.json",
        "models_directory": "responses/models"
    }

    response = client.post("/perfiles/pca/reconstruir", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "model_id" in response.json()
    assert "rebuilt_file" in response.json()
