
import os
import requests
from src.cli import main

# ==========================================
# CONFIGURACIÓN DEL TREN
# ==========================================

ORIGEN = "Toledo"
DESTINO = "Madrid"
FECHA = "11/11/2026"
HORA = "07:25"

# ==========================================
# ENVIAR AVISO A TELEGRAM
# ==========================================

def avisar_telegram(mensaje):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    respuesta = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": mensaje
        },
        timeout=30
    )

    respuesta.raise_for_status()

# ==========================================
# COMPROBAR DISPONIBILIDAD RENFE
# ==========================================

def buscar_tren():

    print(
        f"Buscando {ORIGEN} → {DESTINO} "
        f"el {FECHA} a las {HORA}"
    )

    trenes = main(
        origin=ORIGEN,
        destination=DESTINO,
        departure_date=FECHA,
        from_time=HORA
    )

    if trenes is None:
        raise RuntimeError(
            "No se recibieron resultados de Renfe."
        )

    encontrados = [
        tren for tren in trenes
        if tren.departure_time.strftime("%H:%M") == HORA
    ]

    if not encontrados:
        print("No se encontro el tren solicitado.")
        return

    for tren in encontrados:

        if tren.available:

            mensaje = (
                "🚨🚆 ¡PLAZA RENFE DISPONIBLE!\n\n"
                f"📍 {ORIGEN} → {DESTINO}\n"
                f"📅 Fecha: {FECHA}\n"
                f"🕐 Salida: {HORA}\n\n"
                "🎟️ ¡Entra en Renfe para comprar!\n"
                "https://www.renfe.com"
            )

            avisar_telegram(mensaje)

            print("Alerta enviada a Telegram.")
            return

    print("El tren sigue sin plazas.")


if __name__ == "__main__":
    buscar_tren()
