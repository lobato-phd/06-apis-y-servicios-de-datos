# Dockerfile
FROM python:3.14-slim
WORKDIR /app

# Las dependencias antes que el código: Docker cachea por capas, así cambiar un
# .py no obliga a reinstalarlo todo otra vez.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

# La imagen sirve 07_app.py, la aplicación completa: datos, CRUD, modelo,
# proveedor externo y las dos capas de seguridad.
#
# OJO: aquí NO se definen los secretos a propósito. Un ENV quedaría grabado en la
# imagen y se leería con `docker history`. Se inyectan al arrancar:
#     docker run -e JWT_SECRET="un-secreto-largo" -e API_KEY="otra-clave" \
#                -p 8000:8000 imagen_citas
#
# Sin JWT_SECRET la app se para al arrancar con un mensaje explicando qué falta.
# Sin API_KEY arranca igual, pero /v1/privado responderá 500 al llamarlo.
CMD ["uvicorn", "07_app:app", "--host", "0.0.0.0", "--port", "8000"]
