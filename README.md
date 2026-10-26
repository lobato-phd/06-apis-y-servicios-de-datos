# 06 · APIs y servicios de datos

Código de los laboratorios del Módulo 6 del Máster en Data Engineering, MLOps y Arquitectura Cloud: consumir APIs, construirlas con FastAPI, servir un modelo de ML, hacer scraping con Selenium y llevarlo a producción.

## Puesta en marcha

Requiere Python 3.14 y, para el capítulo 4, Google Chrome.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install requests fastapi uvicorn websockets scikit-learn joblib selenium pyjwt bcrypt python-multipart pytest httpx
```

## Contenido

| Carpeta | Qué hay |
|---|---|
| `01_consumir/` | Consumir APIs REST con `requests` y un pipeline ETL |
| `02_construir/` | FastAPI paso a paso: rutas, Pydantic, CRUD, `response_model` y WebSockets |
| `03_modelos/` | Entrenar un clasificador Iris y servirlo en `/v1/predict` |
| `04_scraping/` | Selenium: localizar, interactuar, esperas, headless y scraper con paginación |
| `05_produccion/` | Robustez, `/health`, API key, CORS, OAuth2 + JWT y la app completa (`07_app.py`) |
| `postman/` | Colección con todas las peticiones (importable en Postman o Bruno) |

## Uso

Cada script indica en su cabecera cómo se ejecuta. Las APIs se arrancan desde su carpeta y se prueban en http://127.0.0.1:8000/docs:

```powershell
cd 02_construir
uvicorn 03_pydantic_y_crud:app --reload
```

La app completa necesita dos variables de entorno:

```powershell
cd 05_produccion
$env:JWT_SECRET = "un-secreto-largo-y-aleatorio"
$env:API_KEY = "clave-secreta-de-prueba"
uvicorn 07_app:app --reload
```

Pruebas, desde `05_produccion` y con `JWT_SECRET` definido: `pytest -v`

Usuario de prueba: `manuel` / `pepito`
