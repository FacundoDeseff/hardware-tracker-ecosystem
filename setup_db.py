import sqlite3
from datetime import datetime

def inicializar_base():
    # Conectamos (o creamos) la base de datos local
    conexion = sqlite3.connect('hardware_tracker.db')
    cursor = conexion.cursor()

    # Tabla 1: Nuestro catálogo (Qué estamos buscando)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS componentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio_objetivo REAL DEFAULT NULL
        )
    ''')

    columnas = {fila[1] for fila in cursor.execute("PRAGMA table_info(componentes)")}
    if 'precio_objetivo' not in columnas:
        cursor.execute('ALTER TABLE componentes ADD COLUMN precio_objetivo REAL DEFAULT NULL')

    # Tabla 2: El historial de precios (A cuánto lo encontramos hoy)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            componente_id INTEGER,
            precio REAL NOT NULL,
            fecha TEXT NOT NULL,
            url_publicacion TEXT,
            FOREIGN KEY (componente_id) REFERENCES componentes (id)
        )
    ''')

    conexion.commit()
    conexion.close()
    print("¡Base de datos 'hardware_tracker.db' creada y lista para operar!")

if __name__ == '__main__':
    inicializar_base()