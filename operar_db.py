import sqlite3

def mostrar_historial():
    conexion = sqlite3.connect("hardware_tracker.db")
    cursor = conexion.cursor()

    consulta = """
        SELECT 
            c.nombre AS componente,
            h.precio,
            h.fecha,
            h.url_publicacion
        FROM historial_precios h
        INNER JOIN componentes c ON h.componente_id = c.id
        ORDER BY h.fecha DESC
    """
    
    cursor.execute(consulta)
    filas = cursor.fetchall()
    conexion.close()

    print("\n📊 HISTORIAL DE PRECIOS REGISTRADOS")
    print("-" * 80)
    print(f"{'Componente':<25} | {'Precio':<12} | {'Fecha':<19} | {'Enlace'}")
    print("-" * 80)

    for comp, precio, fecha, url in filas:
        precio_formateado = f"${precio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        print(f"{comp:<25} | {precio_formateado:<12} | {fecha:<19} | {url[:35]}...")

if __name__ == '__main__':
    mostrar_historial()