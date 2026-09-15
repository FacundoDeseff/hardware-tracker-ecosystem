"""Metadatos inferidos y reglas del asistente de armado."""

import hashlib
import re


CATEGORIA_BUSQUEDA = {
    "cpu": "procesador AMD Ryzen Intel Core",
    "motherboard": "motherboard placa madre AM4 AM5 LGA1700 LGA1851",
    "ram": "memoria RAM DDR4 DDR5",
    "gpu": "placa video RTX RX Radeon GeForce",
    "psu": "fuente poder 500W 650W 750W 850W",
    "storage": "SSD NVMe almacenamiento",
}


def inferir_socket(texto):
    coincidencia = re.search(r"\b(LGA\s?1851|LGA\s?1700|AM5|AM4)\b", texto.upper())
    if coincidencia:
        return coincidencia.group(1).replace(" ", "")
    texto_upper = texto.upper()
    if re.search(r"\b(B550|B450|X570|A520)", texto_upper):
        return "AM4"
    if re.search(r"\b(B650|X670|A620|X870)", texto_upper):
        return "AM5"
    if re.search(r"\b(B760|Z790|H610|B660|H670)", texto_upper):
        return "LGA1700"
    if re.search(r"\b(Z890|B860|H810)", texto_upper):
        return "LGA1851"
    return None


def inferir_ram_type(texto):
    coincidencia = re.search(r"\b(DDR\s?[45])\b", texto.upper())
    return coincidencia.group(1).replace(" ", "") if coincidencia else None


def inferir_tdp(texto, tipo):
    coincidencia = re.search(r"\bTDP\s*[:=]?\s*(\d{2,3})\s?W\b", texto, re.IGNORECASE)
    if coincidencia:
        return int(coincidencia.group(1))

    patrones = {
        "cpu": {
            "5600": 65, "7600": 65, "12400": 65, "13400": 65,
            "14600": 125, "7800x3d": 120, "7950x": 170,
        },
        "gpu": {
            "4060": 115, "4070": 220, "4080": 320, "4090": 450,
            "7600": 165, "7700": 245, "7800": 263,
        },
    }.get(tipo, {})
    texto_lower = texto.lower().replace(" ", "")
    for modelo, tdp in patrones.items():
        if modelo in texto_lower:
            return tdp
    return 0 if tipo in {"motherboard", "psu"} else 50


def inferir_watts_fuente(texto):
    valores = [int(valor) for valor in re.findall(r"\b(\d{3,4})\s?W\b", texto, re.IGNORECASE)]
    return max(valores) if valores else 0


def normalizar_resultado(resultado, tipo):
    texto = f"{resultado.get('titulo', '')} {resultado.get('tienda', '')}"
    enlace = resultado.get("enlace", "")
    base_id = enlace or texto
    identificador = hashlib.sha1(base_id.encode("utf-8")).hexdigest()[:16]
    item = {
        "id": f"real-{identificador}",
        "tipo": tipo,
        "nombre": resultado.get("titulo", "Producto sin nombre"),
        "tienda": resultado.get("tienda", "Tienda no especificada"),
        "precio": float(resultado.get("precio", 0)),
        "imagen": resultado.get("imagen", ""),
        "enlace": enlace,
        "socket": inferir_socket(texto),
        "ram_type": inferir_ram_type(texto),
        "tdp": inferir_tdp(texto, tipo),
        "watts": inferir_watts_fuente(texto) if tipo == "psu" else 0,
    }
    if tipo == "gpu":
        item["psu_watts"] = inferir_watts_fuente(texto)
    return item


def enriquecer_resultados(resultados, tipo):
    return [
        normalizar_resultado(resultado, tipo)
        for resultado in resultados
        if resultado.get("precio", 0) > 0
    ]


def validar_compatibilidad(componentes):
    errores = []
    cpu = componentes.get("cpu")
    motherboard = componentes.get("motherboard")
    ram = componentes.get("ram")
    psu = componentes.get("psu")

    if cpu and motherboard and cpu.get("socket") and motherboard.get("socket") and cpu["socket"] != motherboard["socket"]:
        errores.append("El socket del CPU no coincide con el Motherboard.")
    if motherboard and ram and motherboard.get("ram_type") and ram.get("ram_type") and motherboard["ram_type"] != ram["ram_type"]:
        errores.append("El tipo de memoria RAM no coincide con el Motherboard.")

    consumo_total = sum(int(componente.get("tdp", 0) or 0) for componente in componentes.values()) + 150
    fuente_watts = int(psu.get("watts", 0) or 0) if psu else 0
    if psu and fuente_watts and consumo_total > fuente_watts:
        errores.append(f"La fuente es insuficiente: se estiman {consumo_total}W y ofrece {fuente_watts}W.")

    return {
        "compatible": not errores,
        "errores": errores,
        "consumo_estimado": consumo_total,
        "fuente_watts": fuente_watts,
        "precio_total": sum(float(componente.get("precio", 0) or 0) for componente in componentes.values()),
    }
