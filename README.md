# Hardware Tracker & Alert Ecosystem

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Discord API](https://img.shields.io/badge/Discord-API-5865F2?logo=discord&logoColor=white)](https://discord.com/developers/docs/intro)

Sistema de monitoreo inteligente y automatizado de precios de hardware en Argentina. Hardware Tracker agrega ofertas de distintas tiendas, permite seguir componentes, visualizar su evolución histórica y recibir alertas cuando un precio baja o alcanza un objetivo definido.

## Características principales

- **Búsqueda agregada:** consulta ofertas de hardware mediante HardGamers, con filtros por tienda, ordenamiento por precio y paginación.
- **Seguimiento dinámico:** guarda productos sin recargar la página y permite definir un **Precio Objetivo** para cada componente.
- **Historial de precios:** registra cada actualización en SQLite y ofrece analítica gráfica interactiva con Chart.js.
- **Monitoreo desatendido:** `tracker_cron.py` actualiza precios automáticamente y distingue entre bajadas generales y objetivos alcanzados.
- **Alertas por Discord:** envía Discord Embeds con precio anterior, nuevo precio, ahorro, descuento, tienda e imagen del producto.
- **UI/UX reactiva:** incluye Toasts interactivos, spinners durante el scraping y feedback visual para las operaciones asíncronas.

## Stack tecnológico

- **Backend:** Python, Flask
- **Scraping:** Requests, BeautifulSoup4
- **Persistencia:** SQLite
- **Frontend:** Jinja2, Bootstrap 5.3, JavaScript
- **Gráficos:** Chart.js
- **Automatización y configuración:** `tracker_cron.py`, `python-dotenv`
- **Notificaciones:** Discord Webhook API

## Arquitectura

```text
+-------------------+
| Usuario / Browser |
+---------+---------+
          |
          v
+-------------------+       +-------------------+
| Flask + Jinja2    | ----> | Scraper           |
| app.py            |       | agregador.py      |
+---------+---------+       +---------+---------+
          |                           |
          |                           v
          |                  +-------------------+
          +----------------> | SQLite            |
                             | hardware_tracker  |
                             +---------+---------+
                                       ^
                                       |
                             +---------+---------+
                             | tracker_cron.py   |
                             | Monitoreo periódico|
                             +---------+---------+
                                       |
                                       v
                             +-------------------+
                             | Discord Webhook   |
                             | Alertas y Embeds   |
                             +-------------------+
```

### Flujo de datos

1. El usuario realiza una búsqueda desde la interfaz Flask.
2. `agregador.py` consulta y normaliza las ofertas encontradas.
3. Flask muestra los resultados y permite guardar productos en seguimiento.
4. SQLite conserva componentes, objetivos e historial de precios.
5. `tracker_cron.py` consulta periódicamente los productos seguidos.
6. Si detecta una bajada o un objetivo alcanzado, envía una alerta a Discord.

## Instalación

### Requisitos

- Python 3.10 o superior recomendado.
- Acceso a Internet para consultar las fuentes de precios y Discord.
- Un webhook de Discord para recibir alertas.

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/mercado_hardware.git
cd mercado_hardware
```

### 2. Crear y activar el entorno virtual

En Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

En macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia la plantilla y edítala con tu webhook privado:

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

En macOS/Linux:

```bash
cp .env.example .env
```

El archivo `.env` debe contener:

```dotenv
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/tu_webhook_aqui
```

> No subas `.env` al repositorio. Ya está incluido en `.gitignore`. Comparte únicamente `.env.example` y nunca publiques credenciales o webhooks reales.

## Uso

### Iniciar la aplicación web

```bash
python app.py
```

La aplicación estará disponible en `http://127.0.0.1:5000`.

### Ejecutar el rastreador

Modo normal: consulta los productos seguidos, registra el precio actual y envía alertas cuando corresponde.

```bash
python tracker_cron.py
```

Enviar un Embed de prueba al webhook configurado:

```bash
python tracker_cron.py --test
```

El script puede programarse con el Programador de tareas de Windows, cron o cualquier otro scheduler del sistema.

## Persistencia y datos locales

La aplicación usa `hardware_tracker.db` como base SQLite local. Las tablas principales son:

- `componentes`: nombre, categoría y precio objetivo opcional.
- `historial_precios`: precio, fecha, URL de publicación y componente asociado.

La base se crea o actualiza mediante `setup_db.py`:

```bash
python setup_db.py
```

Las bases SQLite locales están excluidas de Git mediante `.gitignore`.

## Estructura principal

```text
.
├── app.py                 # Aplicación Flask y endpoints HTTP
├── agregador.py           # Scraper y normalización de ofertas
├── tracker_cron.py        # Monitoreo y alertas Discord
├── setup_db.py            # Inicialización y migración SQLite
├── requirements.txt       # Dependencias Python
├── .env.example           # Plantilla de configuración
└── templates/
    ├── index.html         # Buscador y resultados
    └── seguimiento.html   # Productos seguidos y gráficos
```

## Seguridad

- Mantén el webhook real únicamente en `.env`.
- No compartas capturas o logs que expongan la URL del webhook.
- Rota el webhook desde Discord si se publica accidentalmente.
- Revisa los límites y términos de uso de las fuentes consultadas antes de ejecutar el scraper con alta frecuencia.
