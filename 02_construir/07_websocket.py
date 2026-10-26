# 07_websocket.py — WebSockets: cuando la petición-respuesta no basta
#
#     cd 02_construir
#     uvicorn 07_websocket:app --reload --port 8000
#
# Y abrimos http://127.0.0.1:8000/web/ws_demo.html
#
# HTTP tiene una regla que hemos repetido todo el módulo: el cliente pregunta y el
# servidor contesta; el servidor NUNCA empieza la conversación. Eso deja fuera un
# montón de casos — un chat, una notificación, un panel que se actualiza solo — y
# obliga a fingirlos preguntando cada segundo ("polling"), que es caro y va tarde.
#
# Un WebSocket cambia el trato: se abre UNA conexión, se queda abierta, y a partir
# de ahí los dos extremos hablan cuando quieren. Empieza como una petición HTTP
# normal y se "asciende" a WebSocket (por eso la URL es ws:// en vez de http://).
import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Demo de WebSockets", version="1.0")


# --- 1. ECO: el ida y vuelta clásico ---
# Fíjate en las diferencias con un endpoint normal:
#   - el decorador es @app.websocket, no @app.get
#   - la función es async: mientras espera mensajes no bloquea el servidor
#   - hay que aceptar la conexión explícitamente con await ws.accept()
@app.websocket("/ws/eco")
async def eco(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            # receive_text() se queda esperando. No es un bucle que quema CPU:
            # la corrutina se suspende hasta que llega algo.
            mensaje = await ws.receive_text()
            await ws.send_text(f"eco: {mensaje}")
    except WebSocketDisconnect:
        # Cerrar la pestaña es un final NORMAL, no un error. Si no lo capturamos,
        # el log se llena de excepciones cada vez que alguien se va.
        print("Cliente desconectado de /ws/eco")


# --- 2. RELOJ: aquí está la razón de ser de los WebSockets ---
# El servidor envía sin que nadie le pregunte. Con HTTP esto es imposible: haría
# falta que el cliente pidiera la hora cada segundo, una petición completa cada vez
# (con sus cabeceras, su conexión y su latencia) para un dato de ocho caracteres.
@app.websocket("/ws/reloj")
async def reloj(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_text(datetime.now().strftime("%H:%M:%S"))
            # asyncio.sleep, no time.sleep: el time.sleep bloquearía el servidor
            # entero y ningún otro cliente sería atendido durante ese segundo.
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Cliente desconectado de /ws/reloj")


# --- 3. SALA: un mensaje de uno llega a todos ---
# El servidor guarda las conexiones abiertas y reenvía a todas. Eso es un chat, y
# también un panel de control compartido o las notificaciones de una app.
SALA: list[WebSocket] = []


@app.websocket("/ws/sala")
async def sala(ws: WebSocket):
    await ws.accept()
    SALA.append(ws)
    await difundir(f"[alguien ha entrado · {len(SALA)} conectados]")
    try:
        while True:
            mensaje = await ws.receive_text()
            await difundir(mensaje)
    except WebSocketDisconnect:
        # IMPORTANTE: sacar la conexión de la lista al desconectarse. Si no, la
        # lista crece sin parar y el siguiente envío falla sobre un socket muerto.
        SALA.remove(ws)
        await difundir(f"[alguien se ha ido · {len(SALA)} conectados]")


async def difundir(mensaje: str) -> None:
    # Copiamos la lista antes de recorrerla: si un envío falla y quitamos esa
    # conexión, estaríamos modificando la lista mientras la iteramos.
    for conexion in list(SALA):
        try:
            await conexion.send_text(mensaje)
        except Exception:
            SALA.remove(conexion)


# La página de demostración, servida por la misma app: http://127.0.0.1:8000/web/ws_demo.html
app.mount("/web", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")
