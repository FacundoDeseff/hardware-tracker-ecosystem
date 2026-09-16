import sqlite3
from datetime import datetime

DB_PATH = "hardware_tracker.db"

def migrar_y_sembrar():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # 1. Asegurar columnas necesarias en componentes
    columnas_comp = {fila[1] for fila in cursor.execute("PRAGMA table_info(componentes)")}
    if 'imagen_url' not in columnas_comp:
        cursor.execute("ALTER TABLE componentes ADD COLUMN imagen_url TEXT DEFAULT NULL")
    if 'socket' not in columnas_comp:
        cursor.execute("ALTER TABLE componentes ADD COLUMN socket TEXT DEFAULT NULL")
    if 'tdp' not in columnas_comp:
        cursor.execute("ALTER TABLE componentes ADD COLUMN tdp INTEGER DEFAULT 65")

    # 2. Catálogo real de procesadores
    procesadores = [
        # AMD AM4
        ("Microprocesador AMD Ryzen 3 3200G 4.0 GHz AM4", "cpu", "AM4", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_16480_Procesador_AMD_Ryzen_3_3200G_4.0GHz_Turbo___Wraith_Stealth_Cooler_2755e1ca-grn.jpg",
         109155, "https://compragamer.com/producto/procesador-amd-ryzen-3-3200g"),
        ("Procesador AMD Ryzen 5 3600 4.2GHz AM4", "cpu", "AM4", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_15833_Procesador_AMD_RYZEN_5_3600_4.2GHz_Turbo_AM4_Wraith_Stealth_Cooler_407d5705-grn.jpg",
         135000, "https://compragamer.com/producto/procesador-amd-ryzen-5-3600"),
        ("Procesador AMD Ryzen 5 5500 6 Nucleos AM4", "cpu", "AM4", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_31846_Procesador_AMD_Ryzen_5_5500_4.2GHz_Turbo_Wraith_Stealth_Cooler_b58ceca4-grn.jpg",
         144399, "https://compragamer.com/producto/procesador-amd-ryzen-5-5500"),
        ("Procesador AMD Ryzen 5 5600 4.4GHz AM4", "cpu", "AM4", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_32079_Procesador_AMD_Ryzen_5_5600_4.4GHz_Turbo___Wraith_Stealth_Cooler_9b45ff03-grn.jpg",
         169000, "https://compragamer.com/producto/procesador-amd-ryzen-5-5600"),
        ("Procesador AMD Ryzen 5 5600GT 4.6GHz AM4", "cpu", "AM4", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_38890_Procesador_AMD_Ryzen_5_5600GT_4.6GHz_AM4_Wraith_Stealth_Cooler_a4ea7593-grn.jpg",
         175000, "https://compragamer.com/producto/procesador-amd-ryzen-5-5600gt"),
        ("Procesador AMD Ryzen 7 5700X 4.6GHz AM4", "cpu", "AM4", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_32081_Procesador_AMD_Ryzen_7_5700X_4.6GHz_Turbo_AM4_No_Cooler_fa8294eb-grn.jpg",
         225000, "https://compragamer.com/producto/procesador-amd-ryzen-7-5700x"),
        ("Procesador AMD Ryzen 7 5800X 4.7GHz AM4", "cpu", "AM4", 105,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_22394_Procesador_AMD_Ryzen_7_5800X_4.7GHz_Turbo_AM4_No_Cooler_6e0682fa-grn.jpg",
         289000, "https://compragamer.com/producto/procesador-amd-ryzen-7-5800x"),
        ("Procesador AMD Ryzen 7 5700X3D 4.1GHz AM4", "cpu", "AM4", 105,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_38892_Procesador_AMD_Ryzen_7_5700X3D_4.1GHz_AM4_No_Cooler_1fc0fc18-grn.jpg",
         310000, "https://compragamer.com/producto/procesador-amd-ryzen-7-5700x3d"),

        # AMD AM5
        ("Procesador AMD Ryzen 5 7600 5.1GHz AM5", "cpu", "AM5", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_35652_Procesador_AMD_Ryzen_5_7600_5.1GHz_Turbo_AM5_Wraith_Stealth_Cooler_6a382e2c-grn.jpg",
         279000, "https://compragamer.com/producto/procesador-amd-ryzen-5-7600"),
        ("Procesador AMD Ryzen 5 7600X 5.3GHz AM5", "cpu", "AM5", 105,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_34199_Procesador_AMD_Ryzen_5_7600X_5.3GHz_Turbo_AM5_No_Cooler_fa37dc29-grn.jpg",
         315000, "https://compragamer.com/producto/procesador-amd-ryzen-5-7600x"),
        ("Procesador AMD Ryzen 7 7700 5.3GHz AM5", "cpu", "AM5", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_35653_Procesador_AMD_Ryzen_7_7700_5.3GHz_Turbo_AM5_Wraith_Prism_RGB_Cooler_1db3a479-grn.jpg",
         390000, "https://compragamer.com/producto/procesador-amd-ryzen-7-7700"),
        ("Procesador AMD Ryzen 7 7800X3D 5.0GHz AM5", "cpu", "AM5", 120,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_36417_Procesador_AMD_Ryzen_7_7800X3D_5.0GHz_Turbo_AM5_f0a3597b-grn.jpg",
         580000, "https://compragamer.com/producto/procesador-amd-ryzen-7-7800x3d"),

        # INTEL LGA1700
        ("Procesador Intel Core i3 12100F 4.3GHz LGA1700", "cpu", "LGA1700", 58,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_30704_Procesador_Intel_Core_i3_12100F_4.3GHz_Turbo_Socket_1700_Alder_Lake_92e8a157-grn.jpg",
         118000, "https://compragamer.com/producto/procesador-intel-core-i3-12100f"),
        ("Procesador Intel Core i5 12400F 4.4GHz LGA1700", "cpu", "LGA1700", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_30706_Procesador_Intel_Core_i5_12400F_4.4GHz_Turbo_Socket_1700_Alder_Lake_1bb52c21-grn.jpg",
         175000, "https://compragamer.com/producto/procesador-intel-core-i5-12400f"),
        ("Procesador Intel Core i5 13400F 4.6GHz LGA1700", "cpu", "LGA1700", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_35659_Procesador_Intel_Core_i5_13400F_4.6GHz_Turbo_Socket_1700_Raptor_Lake_8c6a0c5b-grn.jpg",
         230000, "https://compragamer.com/producto/procesador-intel-core-i5-13400f"),
        ("Procesador Intel Core i5 14400F 4.7GHz LGA1700", "cpu", "LGA1700", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_38896_Procesador_Intel_Core_i5_14400F_4.7GHz_Turbo_Socket_1700_Raptor_Lake_Refresh_452b4142-grn.jpg",
         256392, "https://compragamer.com/producto/procesador-intel-core-i5-14400f"),
        ("Procesador Intel Core i7 12700KF 5.0GHz LGA1700", "cpu", "LGA1700", 125,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_29699_Procesador_Intel_Core_i7_12700KF_5.0GHz_Turbo_Socket_1700_Alder_Lake_61159931-grn.jpg",
         360000, "https://compragamer.com/producto/procesador-intel-core-i7-12700kf"),
        ("Procesador Intel Core i7 14700F 5.4GHz LGA1700", "cpu", "LGA1700", 65,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_38899_Procesador_Intel_Core_i7_14700F_5.4GHz_Turbo_Socket_1700_Raptor_Lake_Refresh_d5952d7e-grn.jpg",
         480000, "https://compragamer.com/producto/procesador-intel-core-i7-14700f"),

        # INTEL LGA1851
        ("Procesador Intel Core Ultra 5 245KF 5.2GHz LGA1851", "cpu", "LGA1851", 125,
         "https://imagenes.compragamer.com/productos/compragamer_Imganen_general_42100_Procesador_Intel_Core_Ultra_5_245KF_5.2GHz_LGA1851_Arrow_Lake_c50ad852-grn.jpg",
         365750, "https://compragamer.com/producto/procesador-intel-core-ultra-5-245kf")
    ]

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for nombre, cat, socket, tdp, img, precio, url in procesadores:
        cursor.execute("SELECT id FROM componentes WHERE nombre = ?", (nombre,))
        fila = cursor.fetchone()
        if fila:
            comp_id = fila[0]
            cursor.execute("UPDATE componentes SET imagen_url = ?, socket = ?, tdp = ? WHERE id = ?",
                           (img, socket, tdp, comp_id))
        else:
            cursor.execute("INSERT INTO componentes (nombre, categoria, imagen_url, socket, tdp) VALUES (?, ?, ?, ?, ?)",
                           (nombre, cat, img, socket, tdp))
            comp_id = cursor.lastrowid

        cursor.execute("INSERT INTO historial_precios (componente_id, precio, fecha, url_publicacion) VALUES (?, ?, ?, ?)",
                       (comp_id, precio, ahora, url))

    conexion.commit()
    conexion.close()
    print(f"¡Catálogo local actualizado con {len(procesadores)} procesadores reales y completos!")

if __name__ == "__main__":
    migrar_y_sembrar()