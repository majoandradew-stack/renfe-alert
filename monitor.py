
import json
import os
from pathlib import Path

import requests
from src.cli import main

# ==========================================
# CONFIGURACIÓN DEL TREN
# ==========================================

ORIGEN = "Toledo"
DESTINO = "Madrid"
FECHA = "11/11/2026"
HORA = "07:25"

# Archivo para recordar la última disponibilidad
ARCHIVO_ESTADO = Path("state.json")

# Identificador único de esta búsqueda
CLAVE = f"{ORIGEN}|{DESTINO}|{FECHA}|{HORA}"


# ==========================================
# TELEGRAM
# ==========================================

def avisar_telegram(mensaje):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    respuesta = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": mensaje
        },
        timeout=30
    )

    respuesta.raise_for_status()


# ==========================================
# RECORDAR DISPONIBILIDAD
# ==========================================

def leer_estado():
    if not ARCHIVO_ESTADO.exists():
        return {}

    with ARCHIVO_ESTADO.open(
        "r", encoding="utf-8"
    ) as archivo:
        return json.load(archivo)


def guardar_estado(estado):
    with ARCHIVO_ESTADO.open(
        "w", encoding="utf-8"
    ) as archivo:
        json.dump(estado, archivo, indent=2)


# ==========================================
# BUSCAR PLAZAS
# ==========================================

def buscar_tren():
    print(
        f"Buscando {ORIGEN} -> {DESTINO}, "
        f"{FECHA}, {HORA}"
    )

    trenes = main(
        origin=ORIGEN,
        destination=DESTINO,
        departure_date=FECHA,
        from_time=HORA
    )

    # Si la consulta no devuelve resultados,
    # no cambiamos el estado anterior.
    if trenes is None:
        raise RuntimeError(
            "Renfe no devolvió trenes. "
            "No se modifica el estado."
        )

    encontrados = [
        tren for tren in trenes
        if tren.departure_time.strftime("%H:%M") == HORA
    ]

    if not encontrados:
        raise RuntimeError(
            "No se encontró el tren solicitado. "
            "Comprueba fecha y horario."
        )

    disponible = any(
        tren.available for tren in encontrados
    )

    estado = leer_estado()
    disponible_antes = estado.get(CLAVE, False)

    print(f"Disponible ahora: {disponible}")
    print(f"Disponible antes: {disponible_antes}")

    if disponible and not disponible_antes:
        mensaje = (
            "🚨🚆 ¡PLAZA RENFE DISPONIBLE!\n\n"
            f"📍 {ORIGEN} → {DESTINO}\n"
            f"📅 {FECHA}\n"
            f"🕐 Salida: {HORA}\n\n"
            "🎟️ Entra en Renfe para comprar:\n"
            "https://www.renfe.com"
        )

        avisar_telegram(mensaje)
        print("¡Alerta enviada a Telegram!")

    elif disponible:
        print(
            "Sigue disponible. "
            "No se envía una alerta repetida."
        )

    elif disponible_antes:
        print(
            "Se ha agotado nuevamente. "
            "Avisaremos si reaparece."
        )

    else:
        print("Sin plazas disponibles.")

    estado[CLAVE] = disponible
    guardar_estado(estado)


if __name__ == "__main__":
    buscar_tren()

