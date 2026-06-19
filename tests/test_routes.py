import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app import app


def test_read_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "¡uvicorn funciona correctamente!"}


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
