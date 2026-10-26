# crear_usuario.py — da de alta un usuario en el CSV con la contraseña hasheada
#
#     cd 05_produccion
#     python herramientas/crear_usuario.py         (pregunta el usuario)
#     python herramientas/crear_usuario.py ana     (o se lo pasamos como argumento)
#
# Un CSV como almacén de usuarios es de juguete. Lo que NO es de juguete es cómo
# se guarda la contraseña: eso se hace igual en un sistema real.
import csv
import getpass
import sys
from pathlib import Path

import bcrypt

# En la carpeta PADRE: este script vive en herramientas/, pero el CSV lo lee la API.
FICHERO = Path(__file__).parents[1] / "usuarios.csv"


def usuarios_existentes() -> set[str]:
    if not FICHERO.exists():
        return set()
    with FICHERO.open(encoding="utf-8") as f:
        return {fila["username"] for fila in csv.DictReader(f)}


username = sys.argv[1] if len(sys.argv) > 1 else input("Usuario: ")
username = username.strip()

if not username:
    sys.exit("El usuario no puede estar vacío")

# Sin esto, ejecutarlo dos veces con el mismo nombre añade una segunda fila: dos
# usuarios idénticos con contraseñas distintas, y el login solo aceptaría la primera.
if username in usuarios_existentes():
    sys.exit(f"El usuario '{username}' ya existe en {FICHERO.name}")

nombre = input("Nombre completo: ")

# getpass en vez de input: no muestra lo tecleado ni lo deja en el historial de la
# terminal. Da igual lo bien que la guardemos si acaba en claro en el historial.
password = getpass.getpass("Contraseña (no se muestra al teclear): ")

if not password:
    sys.exit("La contraseña no puede estar vacía")

# LA LÍNEA IMPORTANTE: no se guarda la contraseña, se guarda su hash.
#
# gensalt() genera una "sal" distinta por usuario, para que dos personas con la
# misma contraseña tengan hashes distintos. La sal NO es secreta: viaja dentro del
# hash (por eso empieza por $2b$12$). El 12 es el coste, y hace bcrypt lento a
# propósito: a nosotros nos da igual esperar 0,3 s; a quien prueba millones por segundo, no.
hash_ = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

es_nuevo = not FICHERO.exists()
with FICHERO.open("a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if es_nuevo:
        w.writerow(["username", "hash", "nombre"])
    w.writerow([username, hash_, nombre])

print(f"Usuario '{username}' guardado en {FICHERO.name}")
