import requests
from datetime import datetime, timedelta
import random

url = "http://localhost:8080/api/sensors/SP001/data"

for i in range(7):
    timestamp = (datetime.utcnow() - timedelta(days=6 - i)).isoformat()
    data = {
        "rainfall": round(random.uniform(15, 50), 1),
        "water_level": round(random.uniform(60, 120), 1),
        "soil_moisture": round(random.uniform(70, 100), 1),
        "timestamp": timestamp,
        "latitude": -23.5,
        "longitude": -46.63,
    }
    response = requests.post(url, json=data)
    print(f"Dia {i+1}: {response.status_code} - {response.json()}")
