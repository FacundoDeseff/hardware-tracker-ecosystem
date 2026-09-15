import requests
from bs4 import BeautifulSoup

def buscar_hardgamers(producto, ordenar_menor_precio=True):
    print(f"🔎 Buscando '{producto}' en tiendas de Argentina...")
    
    url = f"https://www.hardgamers.com.ar/search?text={producto.replace(' ', '%20')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"❌ Error al conectar: {res.status_code}")
        return []
        
    soup = BeautifulSoup(res.text, 'html.parser')
    articulos = soup.find_all('article')
    
    if not articulos:
        print("⚠️ No se encontraron resultados.")
        return []
        
    resultados = []
    terminos_busqueda = [t.lower() for t in producto.split() if len(t) > 2]
    
    for item in articulos:
        try:
            tienda_tag = item.select_one('.store')
            titulo_tag = item.select_one('.product-name')
            precio_tag = item.select_one('[itemprop="price"]')
            link_tag = item.select_one('a[href]')
            img_tag = item.select_one('img[itemprop="image"]') or item.select_one('img.img')

            if not (tienda_tag and titulo_tag and precio_tag):
                continue

            titulo = titulo_tag.get_text(strip=True)
            titulo_lower = titulo.lower()

            # Filtro básico de pertinencia si la búsqueda tiene términos clave
            coincide = any(t in titulo_lower for t in terminos_busqueda)
            if terminos_busqueda and not coincide:
                continue

            tienda = tienda_tag.get_text(strip=True)
            
            precio_val = precio_tag.get('content') or precio_tag.get_text(strip=True).replace('$', '').replace('.', '').strip()
            precio = float(precio_val)

            enlace = link_tag['href'] if link_tag else ""
            if enlace.startswith('/'):
                enlace = "https://www.hardgamers.com.ar" + enlace

            imagen = ""
            if img_tag:
                for attr in ['data-src', 'data-original', 'src', 'data-lazy']:
                    c = img_tag.get(attr)
                    if c and not c.endswith('.svg') and 'nofound' not in c and 'placeholder' not in c:
                        imagen = c
                        break

            if imagen:
                if imagen.startswith('//'):
                    imagen = "https:" + imagen
                elif imagen.startswith('/'):
                    imagen = "https://www.hardgamers.com.ar" + imagen

            resultados.append({
                "tienda": tienda,
                "titulo": titulo,
                "precio": precio,
                "enlace": enlace,
                "imagen": imagen
            })
        except Exception:
            continue

    if ordenar_menor_precio:
        resultados.sort(key=lambda x: x['precio'])
    else:
        resultados.sort(key=lambda x: x['precio'], reverse=True)

    return resultados

if __name__ == '__main__':
    res = buscar_hardgamers("ddr5", ordenar_menor_precio=True)
    print(f"Total encontrados: {len(res)}")