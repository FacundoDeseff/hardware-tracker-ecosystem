"""Catalogo tecnico y reglas de compatibilidad del PC Builder."""

COMPONENT_CATALOG = [
    {
        "id": "cpu-ryzen-5-5600",
        "tipo": "cpu",
        "nombre": "AMD Ryzen 5 5600",
        "precio": 185000,
        "socket": "AM4",
        "ram_type": "DDR4",
        "tdp": 65,
    },
    {
        "id": "cpu-ryzen-5-7600",
        "tipo": "cpu",
        "nombre": "AMD Ryzen 5 7600",
        "precio": 295000,
        "socket": "AM5",
        "ram_type": "DDR5",
        "tdp": 65,
    },
    {
        "id": "cpu-core-i5-12400f",
        "tipo": "cpu",
        "nombre": "Intel Core i5-12400F",
        "precio": 225000,
        "socket": "LGA1700",
        "ram_type": "DDR4",
        "tdp": 65,
    },
    {
        "id": "cpu-core-i5-14600k",
        "tipo": "cpu",
        "nombre": "Intel Core i5-14600K",
        "precio": 385000,
        "socket": "LGA1700",
        "ram_type": "DDR5",
        "tdp": 125,
    },
    {
        "id": "mb-msi-b550m-pro-vdh",
        "tipo": "motherboard",
        "nombre": "MSI B550M PRO-VDH WIFI",
        "precio": 175000,
        "socket": "AM4",
        "ram_type": "DDR4",
        "tdp": 0,
    },
    {
        "id": "mb-gigabyte-b650m-ds3h",
        "tipo": "motherboard",
        "nombre": "Gigabyte B650M DS3H",
        "precio": 220000,
        "socket": "AM5",
        "ram_type": "DDR5",
        "tdp": 0,
    },
    {
        "id": "mb-asus-b760m-d4",
        "tipo": "motherboard",
        "nombre": "ASUS PRIME B760M-A D4",
        "precio": 205000,
        "socket": "LGA1700",
        "ram_type": "DDR4",
        "tdp": 0,
    },
    {
        "id": "mb-msi-b760m-p",
        "tipo": "motherboard",
        "nombre": "MSI PRO B760M-P DDR5",
        "precio": 215000,
        "socket": "LGA1700",
        "ram_type": "DDR5",
        "tdp": 0,
    },
    {
        "id": "ram-16gb-ddr4-3200",
        "tipo": "ram",
        "nombre": "Kingston Fury 16 GB DDR4 3200",
        "precio": 65000,
        "ram_type": "DDR4",
        "socket": None,
        "tdp": 5,
    },
    {
        "id": "ram-16gb-ddr5-5600",
        "tipo": "ram",
        "nombre": "Kingston Fury 16 GB DDR5 5600",
        "precio": 95000,
        "ram_type": "DDR5",
        "socket": None,
        "tdp": 5,
    },
    {
        "id": "gpu-rtx-4060",
        "tipo": "gpu",
        "nombre": "GeForce RTX 4060 8 GB",
        "precio": 385000,
        "socket": None,
        "ram_type": None,
        "tdp": 115,
        "psu_watts": 550,
    },
    {
        "id": "gpu-rx-7600",
        "tipo": "gpu",
        "nombre": "Radeon RX 7600 8 GB",
        "precio": 365000,
        "socket": None,
        "ram_type": None,
        "tdp": 165,
        "psu_watts": 550,
    },
    {
        "id": "gpu-rtx-4070-super",
        "tipo": "gpu",
        "nombre": "GeForce RTX 4070 SUPER 12 GB",
        "precio": 720000,
        "socket": None,
        "ram_type": None,
        "tdp": 220,
        "psu_watts": 650,
    },
    {
        "id": "psu-500w",
        "tipo": "psu",
        "nombre": "Fuente certificada 500W",
        "precio": 85000,
        "watts": 500,
        "socket": None,
        "ram_type": None,
        "tdp": 0,
    },
    {
        "id": "psu-650w",
        "tipo": "psu",
        "nombre": "Fuente certificada 650W",
        "precio": 125000,
        "watts": 650,
        "socket": None,
        "ram_type": None,
        "tdp": 0,
    },
    {
        "id": "psu-750w",
        "tipo": "psu",
        "nombre": "Fuente certificada 750W",
        "precio": 155000,
        "watts": 750,
        "socket": None,
        "ram_type": None,
        "tdp": 0,
    },
    {
        "id": "psu-850w",
        "tipo": "psu",
        "nombre": "Fuente certificada 850W",
        "precio": 185000,
        "watts": 850,
        "socket": None,
        "ram_type": None,
        "tdp": 0,
    },
    {
        "id": "storage-nvme-1tb",
        "tipo": "storage",
        "nombre": "SSD NVMe 1 TB PCIe 4.0",
        "precio": 95000,
        "socket": None,
        "ram_type": None,
        "tdp": 8,
    },
    {
        "id": "storage-sata-1tb",
        "tipo": "storage",
        "nombre": "SSD SATA 1 TB",
        "precio": 80000,
        "socket": None,
        "ram_type": None,
        "tdp": 5,
    },
]


def obtener_catalogo():
    return [dict(componente) for componente in COMPONENT_CATALOG]


def indexar_catalogo():
    return {componente["id"]: componente for componente in COMPONENT_CATALOG}


def filtrar_opciones(tipo, socket=None, ram_type=None):
    opciones = [componente for componente in COMPONENT_CATALOG if componente["tipo"] == tipo]
    if socket:
        opciones = [opcion for opcion in opciones if opcion.get("socket") in (None, socket)]
    if ram_type:
        opciones = [opcion for opcion in opciones if opcion.get("ram_type") in (None, ram_type)]
    return [dict(opcion) for opcion in opciones]


def validar_compatibilidad(componentes):
    errores = []
    cpu = componentes.get("cpu")
    motherboard = componentes.get("motherboard")
    ram = componentes.get("ram")
    gpu = componentes.get("gpu")
    psu = componentes.get("psu")

    if cpu and motherboard and cpu.get("socket") != motherboard.get("socket"):
        errores.append("El socket del CPU no coincide con el Motherboard.")
    if motherboard and ram and motherboard.get("ram_type") != ram.get("ram_type"):
        errores.append("El tipo de memoria RAM no coincide con el Motherboard.")

    consumo_total = sum(componente.get("tdp", 0) for componente in componentes.values()) + 150
    fuente_watts = psu.get("watts", 0) if psu else 0
    if psu and consumo_total > fuente_watts:
        errores.append(
            f"La fuente es insuficiente: se estiman {consumo_total}W y ofrece {fuente_watts}W."
        )

    return {
        "compatible": not errores,
        "errores": errores,
        "consumo_estimado": consumo_total,
        "fuente_watts": fuente_watts,
        "precio_total": sum(componente.get("precio", 0) for componente in componentes.values()),
    }
