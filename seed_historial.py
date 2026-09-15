import sqlite3
from datetime import datetime, timedelta

DB_PATH = "hardware_tracker.db"


def sembrar_historial():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("SELECT id FROM componentes ORDER BY id LIMIT 1")
    componente = cursor.fetchone()
    if componente is None:
        conexion.close()
        raise RuntimeError("No hay componentes registrados en la base de datos.")

    componente_id = componente[0]
    ahora = datetime.now()
    registros = [
        (componente_id, 820000, ahora - timedelta(days=10)),
        (componente_id, 795000, ahora - timedelta(days=7)),
        (componente_id, 780000, ahora - timedelta(days=4)),
        (componente_id, 775000, ahora - timedelta(days=2)),
        (componente_id, 770000, ahora),
    ]

    cursor.executemany(
        """
        INSERT INTO historial_precios
            (componente_id, precio, fecha, url_publicacion)
        VALUES (?, ?, ?, ?)
        """,
        [
            (componente_id, precio, fecha.strftime("%Y-%m-%d %H:%M:%S"), "seed://historial")
            for componente_id, precio, fecha in registros
        ],
    )

    conexion.commit()
    cantidad = cursor.rowcount
    conexion.close()
    return cantidad


if __name__ == "__main__":
    cantidad = sembrar_historial()
    print(f"Se agregaron {cantidad} registros de prueba.")
