import requests

# ⚠️ Pegá acá los datos de tu App
APP_ID = "2120049869256537"
CLIENT_SECRET = "6yaaTfQm0pkvUT3DcDRHnhWpZTZ0BSr6" 

print("🔐 Solicitando Pase VIP al servidor de MercadoLibre...")

url = "https://api.mercadolibre.com/oauth/token"
payload = {
    "grant_type": "client_credentials",
    "client_id": APP_ID,
    "client_secret": CLIENT_SECRET
}

respuesta = requests.post(url, data=payload)

if respuesta.status_code == 200:
    datos = respuesta.json()
    print("\n✅ ¡TOKEN CONSEGUIDO POR LA FUERZA!")
    print(f"🔑 Tu Token es: {datos['access_token']}")
else:
    print(f"\n❌ Error {respuesta.status_code}:", respuesta.text)