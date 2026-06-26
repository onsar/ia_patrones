import json
import os
from pathlib import Path

import pytest


class FakePCA:
    def inverse_transform(self, comps):
        import numpy as np
        # produce 24 values derived from comps
        val = float(np.sum(comps)) if comps is not None else 0.0
        return np.ones((comps.shape[0], 24)) * (val / (comps.shape[1] if comps.shape[1] else 1))


class FakeScaler:
    def inverse_transform(self, arr):
        import numpy as np
        return np.array(arr) * 1.0


def setup_kmeans_and_model(tmp_path, model_id="m1", kmean_name="ES_TEST_pca7_kmeans24.json"):
    base = tmp_path / "responses"
    kmean_dir = base / "responses_pca" / "kmean1"
    models_dir = base / "models"
    kmean_dir.mkdir(parents=True)
    (models_dir / model_id).mkdir(parents=True)

    # Create kmeans file
    kmeans_file = kmean_dir / kmean_name
    kmeans_data = {
        "input_file": "ES_TEST_2025_01_2025_12.json",
        "model_id": model_id,
        "cluster_centroids": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    }
    kmeans_file.write_text(json.dumps(kmeans_data, ensure_ascii=False))

    # metadata
    metadata = {"training_data": {"source_files": ["ES_TEST_2025_01_2025_12.json"]}}
    metadata_path = models_dir / model_id / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False))

    return str(kmean_dir), str(models_dir), str(kmeans_file)


def test_default_centroides_subdir(tmp_path, monkeypatch):
    kmean_dir, models_dir, kmeans_file = setup_kmeans_and_model(tmp_path)

    import pca_profiles

    def fake_load(model_dir):
        return {"pca_models": [FakePCA()], "scalers": [FakeScaler()]}

    monkeypatch.setattr(pca_profiles, "_load_model_data", fake_load)

    from services import reconstruir_centroides_kmeans_service

    resultado = reconstruir_centroides_kmeans_service(
        directorio=kmean_dir,
        output_directory=kmean_dir,
        file_pattern="*.json",
        models_directory=models_dir,
    )

    assert resultado["status"] == "ok"
    assert resultado["processed_files"] == 1

    outputs = resultado.get("outputs", [])
    assert len(outputs) == 1
    out = outputs[0]
    assert out["status"] == "ok"

    recon_path = out.get("reconstructed_file")
    assert recon_path is not None
    assert os.path.exists(recon_path)

    # ensure saved under centroides1
    assert "/centroides1/" in recon_path.replace("\\", "/")


def test_custom_centroides_subdir(tmp_path, monkeypatch):
    kmean_dir, models_dir, kmeans_file = setup_kmeans_and_model(tmp_path, model_id="m2", kmean_name="ES_TEST2_pca7_kmeans24.json")

    import pca_profiles

    def fake_load(model_dir):
        return {"pca_models": [FakePCA()], "scalers": [FakeScaler()]}

    monkeypatch.setattr(pca_profiles, "_load_model_data", fake_load)

    from services import reconstruir_centroides_kmeans_service

    resultado = reconstruir_centroides_kmeans_service(
        directorio=kmean_dir,
        output_directory=kmean_dir,
        file_pattern="*.json",
        models_directory=models_dir,
        centroides_subdir="centroides_experimentoA",
    )

    assert resultado["status"] == "ok"
    outputs = resultado.get("outputs", [])
    assert len(outputs) == 1
    recon_path = outputs[0].get("reconstructed_file")
    assert recon_path is not None
    assert os.path.exists(recon_path)
    assert "/centroides_experimentoA/" in recon_path.replace("\\", "/")
