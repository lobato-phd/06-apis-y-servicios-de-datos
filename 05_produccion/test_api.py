# test_api.py — pruebas automáticas de la API completa
#
#     cd 05_produccion
#     $env:JWT_SECRET = "un-secreto-largo-y-aleatorio"
#     pytest -v
#
# pytest descubre solo los ficheros que empiezan por test_ y las funciones que
# empiezan por test_. No hay que registrarlas en ninguna parte.
#
# La clave es TestClient: llama a la aplicación EN EL MISMO PROCESO, sin abrir
# ningún puerto ni levantar uvicorn. Por eso una batería entera tarda menos que
# arrancar el servidor a mano.
import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

AQUI = Path(__file__).parent


def cargar_app():
    # 07_app.py empieza por dígito, así que no se puede importar con `import`.
    # Esto es lo mismo que hace uvicorn cuando le decimos `uvicorn 07_app:app`.
    spec = importlib.util.spec_from_file_location("app_completa", AQUI / "07_app.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.app


@pytest.fixture(scope="module")
def cliente():
    # El `with` es lo que dispara el lifespan: sin él, los datos no se cargan
    # y todas las pruebas fallarían con la lista vacía.
    with TestClient(cargar_app()) as c:
        yield c


def test_health_responde_ok(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_listar_citas_devuelve_todas_sin_limite(cliente):
    r = cliente.get("/v1/citas")
    assert r.status_code == 200
    assert r.json()["total"] == len(r.json()["resultados"])


def test_el_listado_no_filtra_id_interno(cliente):
    # La fuga del capítulo 3, convertida en prueba: si alguien quita el
    # response_model, esto se pone rojo.
    assert "id_interno" not in cliente.get("/v1/citas?limite=1").json()["resultados"][0]


def test_cita_inexistente_da_404(cliente):
    assert cliente.get("/v1/citas/99999").status_code == 404


def test_medidas_invalidas_dan_422(cliente):
    r = cliente.post("/v1/predict", json={"largo_sepalo": -1, "ancho_sepalo": 3.5,
                                          "largo_petalo": 1.4, "ancho_petalo": 0.2})
    assert r.status_code == 422


def test_crear_cita_sin_token_da_401(cliente):
    # La regla del 5.11: leer es público, escribir exige credenciales.
    r = cliente.post("/v1/citas", json={"texto": "prueba", "autor": "Nadie"})
    assert r.status_code == 401
