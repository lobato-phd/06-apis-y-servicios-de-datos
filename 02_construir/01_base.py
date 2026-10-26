# 01_base.py — Hello World: nuestro ordenador convertido en servidor
#
#     cd 02_construir
#     uvicorn 01_base:app --reload     (fichero:variable · --reload solo en desarrollo)
#
# Luego abrimos http://127.0.0.1:8000
from fastapi import FastAPI

# `app` es la aplicación que Uvicorn busca y ejecuta. FastAPI escribe la API;
# Uvicorn es el servidor que la mantiene escuchando. Por eso el comando nombra a las dos.
app = FastAPI()


# El decorador conecta un método HTTP (get) y una ruta ("/") con la función de debajo.
@app.get("/")
def raiz():
    return {"mensaje": "Hola, máster"}    # el dict se convierte a JSON solo
