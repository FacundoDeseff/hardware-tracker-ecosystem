import argparse
import os
import sqlite3

import requests
from dotenv import load_dotenv

from agregador import buscar_hardgamers


load_dotenv()

DB_PATH = "hardware_tracker.db"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def asegurar_precio_objetivo(conexion):
    columnas = {fila[1] for fila in conexion.execute("PRAGMA table_info(componentes)")}
    if "precio_objetivo" not in columnas:
        conexion.execute(
            "ALTER TABLE componentes ADD COLUMN precio_objetivo REAL DEFAULT NULL"
        )
        conexion.commit()


def obtener_productos_en_seguimiento(conexion):
    asegurar_precio_objetivo(conexion)
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT c.id, c.nombre, h.url_publicacion, h.precio, c.precio_objetivo
        FROM historial_precios h
        INNER JOIN componentes c ON c.id = h.componente_id
        WHERE h.id IN (
            SELECT MAX(id)
            FROM historial_precios
            WHERE url_publicacion IS NOT NULL
            GROUP BY url_publicacion
        )
        ORDER BY c.id, h.url_publicacion
        """
    )
    return [
        {
            "id": fila[0],
            "nombre": fila[1],
            "url": fila[2],
            "precio_actual": float(fila[3]),
            "precio_objetivo": float(fila[4]) if fila[4] is not None else None,
            "tienda": "",
            "imagen_url": "",
        }
        for fila in cursor.fetchall()
    ]


def obtener_resultado_actual(producto):
    resultados = buscar_hardgamers(producto["nombre"], ordenar_menor_precio=False)
    if not resultados:
        return None

    resultado_url = next(
        (resultado for resultado in resultados if resultado.get("enlace") == producto["url"]),
        None,
    )
    if resultado_url:
        return resultado_url

    nombre_lower = producto["nombre"].lower()
    return next(
        (
            resultado
            for resultado in resultados
            if resultado.get("titulo", "").lower() == nombre_lower
        ),
        None,
    )


def insertar_precio(conexion, componente_id, precio, url):
    conexion.execute(
        """
        INSERT INTO historial_precios
            (componente_id, precio, fecha, url_publicacion)
        VALUES (?, ?, datetime('now', 'localtime'), ?)
        """,
        (componente_id, precio, url),
    )


def enviar_alerta_discord(
    componente, precio_anterior, precio_nuevo, url, tienda, imagen_url="", titulo=None
):
    ahorro = precio_anterior - precio_nuevo
    descuento = (ahorro / precio_anterior * 100) if precio_anterior else 0
    precio_anterior_formateado = f"${precio_anterior:,.2f}"
    precio_nuevo_formateado = f"${precio_nuevo:,.2f}"
    ahorro_formateado = f"${ahorro:,.2f} ({descuento:.2f}%)"

    embed = {
        "title": titulo or "📉 Alerta de bajada de precio",
        "description": f"**{componente['nombre']}**",
        "color": 0x2ECC71,
        "fields": [
            {"name": "Precio Anterior", "value": precio_anterior_formateado, "inline": True},
            {"name": "Nuevo Precio", "value": precio_nuevo_formateado, "inline": True},
            {"name": "Ahorro / % Descuento", "value": ahorro_formateado, "inline": False},
            {"name": "Tienda", "value": tienda or "No especificada", "inline": True},
        ],
        "url": url,
        "footer": {"text": "Mercado Hardware"},
    }
    if imagen_url:
        embed["thumbnail"] = {"url": imagen_url}

    payload = {"embeds": [embed]}
    respuesta = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
    respuesta.raise_for_status()
    return respuesta


def actualizar_y_alertar():
    conexion = sqlite3.connect(DB_PATH)
    productos = obtener_productos_en_seguimiento(conexion)
    actualizados = 0
    alertas = 0

    try:
        for producto in productos:
            resultado = obtener_resultado_actual(producto)
            if resultado is None:
                print(f"Sin precio actualizado: {producto['nombre']}")
                continue

            try:
                precio_nuevo = float(resultado["precio"])
            except (KeyError, TypeError, ValueError):
                print(f"Precio inválido: {producto['nombre']}")
                continue

            if precio_nuevo <= 0:
                print(f"Precio no válido: {producto['nombre']}")
                continue

            precio_anterior = producto["precio_actual"]
            insertar_precio(conexion, producto["id"], precio_nuevo, producto["url"])
            actualizados += 1

            tienda = resultado.get("tienda", "")
            imagen_url = resultado.get("imagen", "")
            precio_objetivo = producto["precio_objetivo"]
            objetivo_alcanzado = (
                precio_objetivo is not None and precio_nuevo <= precio_objetivo
            )
            if objetivo_alcanzado:
                enviar_alerta_discord(
                    producto,
                    precio_anterior,
                    precio_nuevo,
                    producto["url"],
                    tienda,
                    imagen_url,
                    titulo="🎯 ¡Objetivo alcanzado! Precio por debajo del umbral",
                )
                alertas += 1
                print(f"Objetivo alcanzado: {producto['nombre']}")
            elif precio_objetivo is None and precio_nuevo < precio_anterior:
                enviar_alerta_discord(
                    producto,
                    precio_anterior,
                    precio_nuevo,
                    producto["url"],
                    tienda,
                    imagen_url,
                )
                alertas += 1
                print(f"Alerta enviada: {producto['nombre']}")
            else:
                print(f"Precio registrado sin alerta: {producto['nombre']}")

        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

    print(f"Actualizados: {actualizados}. Alertas enviadas: {alertas}.")
    return actualizados, alertas


def test_alerta():
    componente = {"nombre": "Producto de prueba Mercado Hardware"}
    respuesta = enviar_alerta_discord(
        componente=componente,
        precio_anterior=100000,
        precio_nuevo=85000,
        url="https://www.hardgamers.com.ar/",
        tienda="Prueba",
        imagen_url="",
    )
    print(f"Webhook de prueba enviado (HTTP {respuesta.status_code}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actualiza precios y alerta por Discord.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Envía un embed de prueba al webhook de Discord.",
    )
    argumentos = parser.parse_args()

    if argumentos.test:
        test_alerta()
    else:
        actualizar_y_alertar()
