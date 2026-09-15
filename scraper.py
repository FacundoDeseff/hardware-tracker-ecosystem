import re
import sqlite3
import requests
from bs4 import BeautifulSoup

def buscar_precio_fullh4rd(producto):
    print(f"🔎 Buscando '{producto}' en FullH4rd...")
    
    url = f"https://www.fullh4rd.com.ar/cat/search/{producto}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"❌ Error al conectar: {res.status_code}")
        return None
    
    soup = BeautifulSoup(res.text, 'html.parser')
    item = soup.select_one('.item.product-list')
    
    if not item:
        print("❌ No se encontraron productos con ese término.")
        return None
    
    titulo = item.select_one('.info h3').get_text(strip=True)
    precio_texto = item.select_one('.price').get_text(strip=True)
    link = "https://www.fullh4rd.com.ar" + item.select_one('a')['href']
    
    coincidencia = re.search(r'\$?\s*([\d\.]+)(?:,\d+)?', precio_texto)
    if coincidencia:
        monto_str = coincidencia.group(1).replace('.', '')
        precio_limpio = float(monto_str)
    else:
        print("❌ No se pudo parsear el precio.")
        return None
    
    print("\n✅ ¡Producto encontrado con éxito!")
    print(f"📦 Título: {titulo}")
    print(f"💰 Precio: ${precio_limpio}")
    print(f"🔗 Link: {link}")
    
    return {"titulo": titulo, "precio": precio_limpio, "url": link}

def guardar_en_db(componente_id, precio, url_publicacion):
    conexion = sqlite3.connect("hardware_tracker.db")
    cursor = conexion.cursor()
    
    cursor.execute("""
        INSERT INTO historial_precios (componente_id, precio, fecha, url_publicacion)
        VALUES (?, ?, datetime('now', 'localtime'), ?)
    """, (componente_id, precio, url_publicacion))
    
    conexion.commit()
    conexion.close()
    print("💾 Precio guardado en 'historial_precios' exitosamente.")

if __name__ == '__main__':
    datos = buscar_precio_fullh4rd("5060")
    if datos:
        guardar_en_db(
            componente_id=1, 
            precio=datos["precio"], 
            url_publicacion=datos["url"]
        )