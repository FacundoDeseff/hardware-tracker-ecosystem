import math
import sqlite3
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect
from agregador import buscar_hardgamers

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

ITEMS_POR_PAGINA = 12

def asegurar_precio_objetivo(conexion):
    columnas = {fila[1] for fila in conexion.execute("PRAGMA table_info(componentes)")}
    if "precio_objetivo" not in columnas:
        conexion.execute(
            "ALTER TABLE componentes ADD COLUMN precio_objetivo REAL DEFAULT NULL"
        )
        conexion.commit()

def obtener_urls_guardadas():
    conexion = sqlite3.connect("hardware_tracker.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT DISTINCT url_publicacion FROM historial_precios")
    urls = {fila[0] for fila in cursor.fetchall() if fila[0]}
    conexion.close()
    return urls

def registrar_en_db(nombre, precio, url):
    conexion = sqlite3.connect("hardware_tracker.db")
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id FROM componentes WHERE nombre = ?", (nombre,))
    fila = cursor.fetchone()
    
    if fila:
        componente_id = fila[0]
    else:
        cursor.execute("INSERT INTO componentes (nombre, categoria) VALUES (?, ?)", (nombre, "Hardware"))
        componente_id = cursor.lastrowid
        
    cursor.execute("""
        INSERT INTO historial_precios (componente_id, precio, fecha, url_publicacion)
        VALUES (?, ?, datetime('now', 'localtime'), ?)
    """, (componente_id, precio, url))
    
    conexion.commit()
    conexion.close()

def eliminar_de_db(url):
    conexion = sqlite3.connect("hardware_tracker.db")
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM historial_precios WHERE url_publicacion = ?", (url,))
    conexion.commit()
    conexion.close()

def obtener_favoritos_unicos():
    conexion = sqlite3.connect("hardware_tracker.db")
    asegurar_precio_objetivo(conexion)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT c.id, c.nombre, h.precio, h.fecha, h.url_publicacion,
               c.precio_objetivo
        FROM historial_precios h
        INNER JOIN componentes c ON h.componente_id = c.id
        WHERE h.id IN (
            SELECT MAX(id) FROM historial_precios GROUP BY url_publicacion
        )
        ORDER BY h.fecha DESC
    """)
    filas = cursor.fetchall()
    conexion.close()
    return filas

@app.route("/api/historial/<int:componente_id>")
def historial_componente(componente_id):
    conexion = sqlite3.connect("hardware_tracker.db")
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT fecha, precio
        FROM historial_precios
        WHERE componente_id = ?
        ORDER BY fecha ASC, id ASC
    """, (componente_id,))
    filas = cursor.fetchall()
    conexion.close()

    return jsonify({
        "fechas": [fila[0] for fila in filas],
        "precios": [fila[1] for fila in filas]
    })

@app.route("/api/seguimiento/<int:componente_id>/objetivo", methods=["POST"])
def actualizar_precio_objetivo(componente_id):
    datos = request.get_json(silent=True)
    if datos is None or "precio_objetivo" not in datos:
        return jsonify({"status": "error", "mensaje": "Precio objetivo no válido"}), 400

    precio_objetivo = datos["precio_objetivo"]
    if precio_objetivo is not None:
        try:
            precio_objetivo = float(precio_objetivo)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "mensaje": "Precio objetivo no válido"}), 400
        if precio_objetivo < 0:
            return jsonify({"status": "error", "mensaje": "El precio objetivo no puede ser negativo"}), 400

    conexion = sqlite3.connect("hardware_tracker.db")
    try:
        asegurar_precio_objetivo(conexion)
        cursor = conexion.execute(
            "UPDATE componentes SET precio_objetivo = ? WHERE id = ?",
            (precio_objetivo, componente_id),
        )
        if cursor.rowcount == 0:
            conexion.rollback()
            return jsonify({"status": "error", "mensaje": "Componente no encontrado"}), 404
        conexion.commit()
    finally:
        conexion.close()

    return jsonify({"status": "ok", "precio_objetivo": precio_objetivo})

@app.route("/", methods=["GET", "POST"])
def index():
    busqueda = request.args.get("q", request.args.get("producto", "")).strip()
    tienda = request.args.get("tienda", "").strip()
    orden = request.args.get("orden", "")
    pagina_actual = request.values.get("page", 1, type=int) or 1

    resultados_pagina = []
    total_paginas = 1
    total_items = 0

    if busqueda:
        todos_los_resultados = buscar_hardgamers(
            producto=busqueda, 
            ordenar_menor_precio=(orden != "desc")
        )

        if tienda:
            tienda_buscada = tienda.casefold()
            todos_los_resultados = [
                item for item in todos_los_resultados
                if item.get("tienda", "").casefold() == tienda_buscada
            ]

        if orden == "asc":
            todos_los_resultados.sort(key=lambda item: item.get("precio", float("inf")))
        elif orden == "desc":
            todos_los_resultados.sort(
                key=lambda item: item.get("precio", float("-inf")),
                reverse=True,
            )

        total_items = len(todos_los_resultados)
        total_paginas = math.ceil(total_items / ITEMS_POR_PAGINA) or 1

        # Validamos rango de página
        if pagina_actual < 1:
            pagina_actual = 1
        elif pagina_actual > total_paginas:
            pagina_actual = total_paginas

        # Segmentamos para la página actual
        inicio = (pagina_actual - 1) * ITEMS_POR_PAGINA
        fin = inicio + ITEMS_POR_PAGINA
        resultados_pagina = todos_los_resultados[inicio:fin]

    urls_guardadas = obtener_urls_guardadas()

    return render_template(
        "index.html", 
        resultados=resultados_pagina, 
        busqueda=busqueda, 
        tienda=tienda,
        orden=orden,
        urls_guardadas=urls_guardadas,
        pagina_actual=pagina_actual,
        total_paginas=total_paginas,
        total_items=total_items
    )

@app.route("/seguimiento")
def seguimiento():
    historial = obtener_favoritos_unicos()
    return render_template("seguimiento.html", historial=historial)

@app.route("/toggle_seguimiento", methods=["POST"])
def toggle_seguimiento():
    datos = request.get_json()
    if not datos:
        return jsonify({"status": "error", "mensaje": "Datos no válidos"}), 400
        
    url = datos.get("enlace")
    accion = datos.get("accion")
    
    if accion == "guardar":
        registrar_en_db(
            nombre=datos.get("titulo"),
            precio=float(datos.get("precio")),
            url=url
        )
        return jsonify({"status": "ok", "estado": "guardado"})
    elif accion == "eliminar":
        eliminar_de_db(url)
        return jsonify({"status": "ok", "estado": "eliminado"})
    
    return jsonify({"status": "error", "mensaje": "Acción desconocida"}), 400

@app.route("/ir_a_tienda")
def ir_a_tienda():
    url_hardgamers = request.args.get("url")
    if not url_hardgamers:
        return redirect("/")

    try:
        res = requests.get(url_hardgamers, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            texto = a.text.strip().lower()
            if 'tienda' in texto or 'ver producto' in texto:
                return redirect(a['href'])
                
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and not any(d in href for d in ['hardgamers', 'facebook', 'instagram', 'twitter']):
                return redirect(href)

    except Exception:
        pass

    return redirect(url_hardgamers)

if __name__ == "__main__":
    app.run(debug=True, port=5000)