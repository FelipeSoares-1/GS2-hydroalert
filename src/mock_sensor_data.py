import requests
from datetime import datetime, timedelta
import random

sensores = {
    "SP001": (-23.5, -46.63),
    "RJ001": (-22.91, -43.23),
    "BL001": (-26.91, -49.06),
    "PE001": (-8.12, -34.90),
    "RS001": (-30.03, -51.18),
}

for sensor_id, (lat, lon) in sensores.items():
    print(f"📡 Inserindo dados para {sensor_id}")
    for i in range(7):
        timestamp = (datetime.utcnow() - timedelta(days=6 - i)).isoformat()
        data = {
            "rainfall": round(random.uniform(15, 50), 1),
            "water_level": round(random.uniform(60, 120), 1),
            "soil_moisture": round(random.uniform(70, 100), 1),
            "timestamp": timestamp,
            "latitude": lat,
            "longitude": lon,
        }
        response = requests.post(
            f"http://localhost:8080/api/sensors/{sensor_id}/data", json=data
        )
        print(f"  Dia {i+1}: {response.status_code} - {response.json()['status']}")
