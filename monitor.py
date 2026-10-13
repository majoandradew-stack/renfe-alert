
import json
import os
from datetime import datetime
from pathlib import Path

import requests
from src.cli import main

# ==========================================
# TUS ALERTAS: EDITA SOLO ESTA LISTA
# ==========================================

ALERTAS = [
    {
        "origen": "Toledo",
        "destino": "Madrid Pta. Atocha - Almudena Grandes",
        "fecha": "25/11/2026",
        "hora": "07:25",
    },
    {
        "origen": "Toledo",
        "destino": "Madrid Pta. Atocha - Almudena Grandes",
        "fecha": "14/10/2026",
        "hora": "18:45",
    },
]

ARCHIVO_ESTADO = Path("state.json")


def avisar_telegram(mensaje):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    respuesta = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": mensaje,
        },
        timeout=30,
    )
    respuesta.raise_for_status()


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
        json.dump(
            estado,
            archivo,
            indent=2,
            ensure_ascii=False,
        )


def comprobar_alerta(alerta, estado):
    origen = alerta["origen"]
    destino = alerta["destino"]
    fecha = alerta["fecha"]
    hora = alerta["hora"]

    clave = f"{origen}|{destino}|{fecha}|{hora}"

    print(f"\nBuscando {origen} -> {destino}")
    print(f"Fecha: {fecha}, hora: {hora}")

    fecha_tren = datetime.strptime(
        f"{fecha} {hora}", "%d/%m/%Y %H:%M"
    )

    if fecha_tren <= datetime.now():
        print("Tren pasado. Se omite.")
        return

    trenes = main(
        origin=origen,
        destination=destino,
        departure_date=fecha,
        from_time=hora,
    )

    if trenes is None:
        raise RuntimeError(
            "Renfe no devolvió trenes para esta búsqueda."
        )

    encontrados = [
        tren
        for tren in trenes
        if tren.departure_time.strftime("%H:%M") == hora
    ]

    if not encontrados:
        raise RuntimeError(
            "No se encontró un tren con esa hora exacta."
        )

    disponible = any(
        tren.available for tren in encontrados
    )

    disponible_antes = estado.get(clave, False)

    print(f"Disponible ahora: {disponible}")
    print(f"Disponible antes: {disponible_antes}")

    if disponible and not disponible_antes:
        mensaje = (
            "🚨🚆 ¡PLAZA RENFE DISPONIBLE!\n\n"
            f"📍 {origen} → {destino}\n"
            f"📅 {fecha}\n"
            f"🕐 Salida: {hora}\n\n"
            "🎟️ Compra tu billete:\n"
            "https://www.renfe.com"
        )

        avisar_telegram(mensaje)
        print("¡Alerta enviada a Telegram!")

    elif disponible:
        print(
            "Sigue disponible. No se repite la alerta."
        )

    elif disponible_antes:
        print(
            "Se agotó nuevamente. "
            "Avisaremos si reaparecen plazas."
        )

    else:
        print("Sin plazas disponibles.")

    estado[clave] = disponible
    guardar_estado(estado)


def buscar_trenes():
    estado = leer_estado()
    errores = []

    for alerta in ALERTAS:
        try:
            comprobar_alerta(alerta, estado)

        except Exception as error:
            descripcion = (
                f"{alerta['fecha']} "
                f"{alerta['hora']}: {error}"
            )
            print(f"ERROR: {descripcion}")
            errores.append(descripcion)

    if errores:
        raise RuntimeError(
            "Algunas búsquedas fallaron:\n"
            + "\n".join(errores)
        )

    print("\nComprobación finalizada correctamente.")


if __name__ == "__main__":
    buscar_trenes()


