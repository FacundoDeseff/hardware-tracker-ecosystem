import math
import sqlite3
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect
from agregador import buscar_hardgamers
from pc_builder import CATEGORIA_BUSQUEDA, clasificar_tipo, enriquecer_resultados, validar_compatibilidad

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

ITEMS_POR_PAGINA = 12
BUILDER_OPTIONS_CACHE = {}

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

@app.route("/builder")
def builder():
    return render_template("builder.html")

@app.route("/api/builder/options")
def builder_options():
    tipo = request.args.get("tipo", "").strip().lower()
    busqueda = request.args.get("q", "").strip()
    socket = request.args.get("socket", "").strip()
    ram_type = request.args.get("ram_type", "").strip()
    recommended_watts = request.args.get("recommended_watts", type=int)
    if tipo not in CATEGORIA_BUSQUEDA:
        return jsonify({"status": "error", "mensaje": "Categoría no válida"}), 400

    if tipo == "cpu":
        consulta = f"procesador {busqueda or 'Ryzen'}"
    elif tipo == "motherboard":
        consulta = f"motherboard {socket}" if socket else f"motherboard {busqueda}".strip()
    elif tipo == "ram":
        consulta = f"memoria {ram_type}" if ram_type else f"memoria {busqueda}".strip()
    elif tipo == "gpu":
        consulta = f"placa de video {busqueda or 'RTX RX'}"
    elif tipo == "psu":
        consulta = f"fuente de poder {busqueda or '650W'}"
    else:
        consulta = f"SSD {busqueda or 'NVMe'}"

    try:
        resultados = buscar_hardgamers(consulta, ordenar_menor_precio=True)
    except Exception:
        resultados = []
    opciones = enriquecer_resultados(resultados, tipo)
    if socket:
        opciones = [opcion for opcion in opciones if opcion.get("socket") == socket]
    if ram_type:
        opciones = [opcion for opcion in opciones if opcion.get("ram_type") == ram_type]
    if tipo == "psu" and recommended_watts:
        opciones = [opcion for opcion in opciones if opcion.get("watts", 0) >= recommended_watts]
    if not opciones:
        opciones = obtener_opciones_locales(tipo, socket, ram_type, recommended_watts)
    for opcion in opciones:
        BUILDER_OPTIONS_CACHE[opcion["id"]] = opcion
    return jsonify({"status": "ok", "opciones": opciones})


def obtener_opciones_locales(tipo, socket=None, ram_type=None, recommended_watts=None):
    conexion = sqlite3.connect("hardware_tracker.db")
    try:
        filas = conexion.execute("""
            SELECT h.url_publicacion, c.nombre, h.precio
            FROM historial_precios h
            INNER JOIN componentes c ON c.id = h.componente_id
            WHERE h.id IN (
                SELECT MAX(id) FROM historial_precios
                WHERE url_publicacion IS NOT NULL
                GROUP BY url_publicacion
            )
            ORDER BY h.fecha DESC
            LIMIT 80
        """).fetchall()
    finally:
        conexion.close()

    resultados = []
    for url, nombre, precio in filas:
        if clasificar_tipo(nombre) != tipo:
            continue
        opcion = enriquecer_resultados([{
            "titulo": nombre,
            "tienda": "Guardado local",
            "precio": precio,
            "enlace": url,
            "imagen": "",
        }], tipo)[0]
        if socket and opcion.get("socket") and opcion["socket"] != socket:
            continue
        if ram_type and opcion.get("ram_type") and opcion["ram_type"] != ram_type:
            continue
        if recommended_watts and tipo == "psu" and opcion.get("watts", 0) < recommended_watts:
            continue
        resultados.append(opcion)
    for opcion in resultados:
        BUILDER_OPTIONS_CACHE[opcion["id"]] = opcion
    return resultados


def componentes_seleccionados(seleccionados):
    componentes = {}
    for tipo, seleccion in seleccionados.items():
        if not seleccion:
            continue
        componente = BUILDER_OPTIONS_CACHE.get(seleccion) if isinstance(seleccion, str) else seleccion
        if not isinstance(componente, dict) or componente.get("tipo") != tipo:
            continue
        try:
            componente = dict(componente)
            componente["precio"] = float(componente.get("precio", 0))
            componente["tdp"] = int(componente.get("tdp", 0) or 0)
            componente["watts"] = int(componente.get("watts", 0) or 0)
        except (TypeError, ValueError):
            continue
        componentes[tipo] = componente
    return componentes

@app.route("/api/builder/validate", methods=["POST"])
def builder_validate():
    datos = request.get_json(silent=True) or {}
    seleccionados = datos.get("componentes", datos)
    componentes = componentes_seleccionados(seleccionados)
    errores = [f"La selección de {tipo} no es válida." for tipo in seleccionados if seleccionados.get(tipo) and tipo not in componentes]

    resultado = validar_compatibilidad(componentes)
    resultado["errores"] = errores + resultado["errores"]
    resultado["compatible"] = not resultado["errores"]
    resultado["componentes"] = componentes
    return jsonify({"status": "ok", **resultado})

@app.route("/api/builder/save", methods=["POST"])
def builder_save():
    datos = request.get_json(silent=True) or {}
    seleccionados = datos.get("componentes", datos)
    componentes = componentes_seleccionados(seleccionados)
    guardados = 0
    for componente in componentes.values():
        registrar_en_db(
            nombre=f"[Build] {componente['nombre']}",
            precio=float(componente["precio"]),
            url=componente.get("enlace") or f"builder://{componente['id']}",
        )
        guardados += 1
    if not guardados:
        return jsonify({"status": "error", "mensaje": "No hay componentes seleccionados"}), 400
    return jsonify({"status": "ok", "guardados": guardados})

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