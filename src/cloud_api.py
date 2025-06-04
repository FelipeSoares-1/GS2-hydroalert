"""
Sistema de Computação em Nuvem para HydroAlert
Global Solution 2025.1 - FIAP
Grupo 35 - Componente de Cloud Computing

Integração com serviços cloud para:
- API REST para dados em tempo real
- Armazenamento de dados na nuvem
- Deploy automatizado
- Monitoramento e alertas
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime, timedelta
import requests
import threading
import time
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd

# Configurações da aplicação
app = Flask(__name__)
CORS(app)

@dataclass
class SensorReading:
    """Estrutura de dados para leitura de sensores"""
    sensor_id: str
    timestamp: str
    rainfall: float
    water_level: float
    soil_moisture: float
    latitude: float
    longitude: float

class CloudDatabase:
    """
    Classe para gerenciar banco de dados SQLite local
    Em produção seria substituído por serviços cloud como RDS/CosmosDB
    """
    
    def __init__(self, db_path="data/hydroalert_cloud.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa estrutura do banco de dados"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de sensores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de leituras dos sensores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                rainfall REAL NOT NULL,
                water_level REAL NOT NULL,
                soil_moisture REAL NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES sensors (id)
            )
        """)
        
        # Tabela de previsões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                prediction_time TIMESTAMP NOT NULL,
                flood_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                model_version TEXT DEFAULT 'v1.0',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES sensors (id)
            )
        """)
        
        # Tabela de alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES sensors (id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Inserir sensores de exemplo se não existirem
        self.insert_sample_sensors()
    
    def insert_sample_sensors(self):
        """Insere sensores de exemplo no banco"""
        sample_sensors = [
            ("SP001", "São Paulo - Zona Norte", -23.5, -46.63),
            ("RJ001", "Rio de Janeiro - Maracanã", -22.91, -43.23),
            ("BL001", "Blumenau - Centro", -26.91, -49.06),
            ("PE001", "Recife - Boa Viagem", -8.12, -34.90),
            ("RS001", "Porto Alegre - Sarandi", -30.03, -51.18)
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for sensor_id, name, lat, lon in sample_sensors:
            cursor.execute("""
                INSERT OR IGNORE INTO sensors (id, name, latitude, longitude)
                VALUES (?, ?, ?, ?)
            """, (sensor_id, name, lat, lon))
        
        conn.commit()
        conn.close()
    
    def insert_sensor_reading(self, reading: SensorReading):
        """Insere nova leitura de sensor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sensor_readings 
            (sensor_id, timestamp, rainfall, water_level, soil_moisture)
            VALUES (?, ?, ?, ?, ?)
        """, (reading.sensor_id, reading.timestamp, reading.rainfall, 
              reading.water_level, reading.soil_moisture))
        
        conn.commit()
        conn.close()
    
    def get_recent_readings(self, sensor_id: str = None, hours: int = 24) -> List[Dict]:
        """Recupera leituras recentes"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT r.*, s.name, s.latitude, s.longitude
            FROM sensor_readings r
            JOIN sensors s ON r.sensor_id = s.id
            WHERE r.timestamp >= datetime('now', '-{} hours')
        """.format(hours)
        
        params = []
        if sensor_id:
            query += " AND r.sensor_id = ?"
            params.append(sensor_id)
        
        query += " ORDER BY r.timestamp DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df.to_dict('records')

# Instância do banco de dados
db = CloudDatabase()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "HydroAlert Cloud API",
        "version": "1.0.0"
    })

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """Lista todos os sensores cadastrados"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sensors WHERE status = 'active'")
    sensors = cursor.fetchall()
    conn.close()
    
    result = []
    for sensor in sensors:
        result.append({
            "id": sensor[0],
            "name": sensor[1],
            "latitude": sensor[2],
            "longitude": sensor[3],
            "status": sensor[4],
            "created_at": sensor[5]
        })
    
    return jsonify({
        "sensors": result,
        "count": len(result)
    })

@app.route('/api/sensors/<sensor_id>/data', methods=['POST'])
def receive_sensor_data(sensor_id):
    """Recebe dados dos sensores ESP32"""
    try:
        data = request.get_json()
        
        # Validar dados recebidos
        required_fields = ['rainfall', 'water_level', 'soil_moisture']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo obrigatório missing: {field}"}), 400
        
        # Criar objeto de leitura
        reading = SensorReading(
            sensor_id=sensor_id,
            timestamp=data.get('timestamp', datetime.utcnow().isoformat()),
            rainfall=float(data['rainfall']),
            water_level=float(data['water_level']),
            soil_moisture=float(data['soil_moisture']),
            latitude=data.get('latitude', 0.0),
            longitude=data.get('longitude', 0.0)
        )
        
        # Salvar no banco
        db.insert_sensor_reading(reading)
        
        # Processar dados para previsão (em background)
        threading.Thread(target=process_prediction, args=(sensor_id, reading)).start()
        
        return jsonify({
            "status": "success",
            "message": "Dados recebidos com sucesso",
            "sensor_id": sensor_id,
            "timestamp": reading.timestamp
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensors/<sensor_id>/readings', methods=['GET'])
def get_sensor_readings(sensor_id):
    """Recupera leituras de um sensor específico"""
    hours = request.args.get('hours', 24, type=int)
    
    readings = db.get_recent_readings(sensor_id, hours)
    
    return jsonify({
        "sensor_id": sensor_id,
        "readings": readings,
        "count": len(readings),
        "period_hours": hours
    })

@app.route('/api/readings/recent', methods=['GET'])
def get_recent_readings():
    """Recupera todas as leituras recentes"""
    hours = request.args.get('hours', 24, type=int)
    
    readings = db.get_recent_readings(hours=hours)
    
    return jsonify({
        "readings": readings,
        "count": len(readings),
        "period_hours": hours
    })

@app.route('/api/predictions/<sensor_id>', methods=['GET'])
def get_predictions(sensor_id):
    """Recupera previsões para um sensor"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM predictions 
        WHERE sensor_id = ? 
        ORDER BY prediction_time DESC 
        LIMIT 10
    """, (sensor_id,))
    
    predictions = cursor.fetchall()
    conn.close()
    
    result = []
    for pred in predictions:
        result.append({
            "id": pred[0],
            "sensor_id": pred[1],
            "prediction_time": pred[2],
            "flood_probability": pred[3],
            "risk_level": pred[4],
            "model_version": pred[5],
            "created_at": pred[6]
        })
    
    return jsonify({
        "sensor_id": sensor_id,
        "predictions": result,
        "count": len(result)
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Recupera alertas ativos"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, s.name as sensor_name
        FROM alerts a
        JOIN sensors s ON a.sensor_id = s.id
        WHERE a.acknowledged = FALSE
        ORDER BY a.timestamp DESC
    """)
    
    alerts = cursor.fetchall()
    conn.close()
    
    result = []
    for alert in alerts:
        result.append({
            "id": alert[0],
            "sensor_id": alert[1],
            "sensor_name": alert[8],
            "alert_type": alert[2],
            "message": alert[3],
            "severity": alert[4],
            "timestamp": alert[5],
            "acknowledged": alert[6],
            "created_at": alert[7]
        })
    
    return jsonify({
        "alerts": result,
        "count": len(result)
    })

@app.route('/api/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Endpoint para dados do dashboard"""
    conn = sqlite3.connect(db.db_path)
    
    # Total de sensores ativos
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sensors WHERE status = 'active'")
    total_sensors = cursor.fetchone()[0]
    
    # Alertas ativos
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = FALSE")
    active_alerts = cursor.fetchone()[0]
    
    # Leituras das últimas 24h
    cursor.execute("""
        SELECT COUNT(*) FROM sensor_readings 
        WHERE timestamp >= datetime('now', '-24 hours')
    """)
    readings_24h = cursor.fetchone()[0]
    
    # Previsões de risco alto
    cursor.execute("""
        SELECT COUNT(*) FROM predictions 
        WHERE risk_level IN ('ALTO', 'CRÍTICO')
        AND prediction_time >= datetime('now', '-1 hours')
    """)
    high_risk_predictions = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "summary": {
            "total_sensors": total_sensors,
            "active_alerts": active_alerts,
            "readings_24h": readings_24h,
            "high_risk_predictions": high_risk_predictions
        },
        "timestamp": datetime.utcnow().isoformat()
    })

# =============================================================================
# PROCESSAMENTO DE PREVISÕES
# =============================================================================

def process_prediction(sensor_id: str, reading: SensorReading):
    """
    Processa dados do sensor e gera previsões
    Em produção seria integrado com modelo ML na nuvem
    """
    try:
        # Simulação de processamento de ML
        # Em produção seria chamada para serviço ML na nuvem
        
        # Calcular probabilidade baseada em regras simples
        flood_probability = 0.0
        
        if reading.rainfall > 15:
            flood_probability += 0.3
        if reading.water_level > 80:
            flood_probability += 0.4
        if reading.soil_moisture > 90:
            flood_probability += 0.2
        
        # Combinar fatores
        flood_probability = min(flood_probability, 1.0)
        
        # Determinar nível de risco
        if flood_probability < 0.3:
            risk_level = "BAIXO"
        elif flood_probability < 0.6:
            risk_level = "MODERADO"
        elif flood_probability < 0.8:
            risk_level = "ALTO"
        else:
            risk_level = "CRÍTICO"
        
        # Salvar previsão
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO predictions 
            (sensor_id, prediction_time, flood_probability, risk_level)
            VALUES (?, ?, ?, ?)
        """, (sensor_id, datetime.utcnow().isoformat(), flood_probability, risk_level))
        
        # Gerar alerta se necessário
        if risk_level in ["ALTO", "CRÍTICO"]:
            message = f"Risco {risk_level} de inundação detectado no sensor {sensor_id}"
            cursor.execute("""
                INSERT INTO alerts 
                (sensor_id, alert_type, message, severity, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (sensor_id, "FLOOD_RISK", message, risk_level, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Erro no processamento de previsão: {e}")

# =============================================================================
# CONFIGURAÇÕES PARA DEPLOY
# =============================================================================

class CloudConfig:
    """Configurações para deploy em nuvem"""
    
    @staticmethod
    def get_deployment_config():
        """Retorna configuração para deploy"""
        return {
            "app_name": "hydroalert-api",
            "runtime": "python3.10",
            "instance_class": "F2",
            "automatic_scaling": {
                "min_instances": 1,
                "max_instances": 10,
                "target_cpu_utilization": 0.6
            },
            "environment_variables": {
                "FLASK_ENV": "production",
                "DATABASE_URL": "sqlite:///data/hydroalert_cloud.db"
            },
            "health_check": "/api/health"
        }
    
    @staticmethod
    def create_dockerfile():
        """Cria Dockerfile para containerização"""
        dockerfile_content = """
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "src/cloud_api.py"]
"""
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
    
    @staticmethod
    def create_requirements():
        """Cria requirements.txt para a API"""
        requirements = """
flask==2.3.3
flask-cors==4.0.0
pandas==1.5.3
sqlite3
requests==2.31.0
gunicorn==21.2.0
"""
        with open("requirements_cloud.txt", "w") as f:
            f.write(requirements)

def create_monitoring_dashboard():
    """
    Cria dashboard de monitoramento da API
    """
    monitoring_html = """
<!DOCTYPE html>
<html>
<head>
    <title>HydroAlert Cloud Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { display: inline-block; margin: 10px; padding: 20px; 
                 border: 1px solid #ccc; border-radius: 5px; }
        .metric h3 { margin: 0 0 10px 0; color: #333; }
        .metric .value { font-size: 24px; font-weight: bold; color: #2196F3; }
        .status-ok { color: #4CAF50; }
        .status-warning { color: #FF9800; }
        .status-error { color: #F44336; }
    </style>
</head>
<body>
    <h1>🌊 HydroAlert Cloud API Monitor</h1>
    
    <div id="metrics">
        <div class="metric">
            <h3>Status da API</h3>
            <div class="value" id="api-status">Verificando...</div>
        </div>
        
        <div class="metric">
            <h3>Sensores Ativos</h3>
            <div class="value" id="sensors-count">-</div>
        </div>
        
        <div class="metric">
            <h3>Alertas Ativos</h3>
            <div class="value" id="alerts-count">-</div>
        </div>
        
        <div class="metric">
            <h3>Leituras (24h)</h3>
            <div class="value" id="readings-count">-</div>
        </div>
    </div>
    
    <script>
        async function updateMetrics() {
            try {
                // Verificar saúde da API
                const healthResponse = await fetch('/api/health');
                const healthStatus = document.getElementById('api-status');
                
                if (healthResponse.ok) {
                    healthStatus.textContent = 'Online';
                    healthStatus.className = 'value status-ok';
                } else {
                    healthStatus.textContent = 'Offline';
                    healthStatus.className = 'value status-error';
                }
                
                // Buscar resumo do dashboard
                const summaryResponse = await fetch('/api/dashboard/summary');
                if (summaryResponse.ok) {
                    const data = await summaryResponse.json();
                    const summary = data.summary;
                    
                    document.getElementById('sensors-count').textContent = summary.total_sensors;
                    document.getElementById('alerts-count').textContent = summary.active_alerts;
                    document.getElementById('readings-count').textContent = summary.readings_24h;
                }
                
            } catch (error) {
                console.error('Erro ao atualizar métricas:', error);
                document.getElementById('api-status').textContent = 'Erro';
                document.getElementById('api-status').className = 'value status-error';
            }
        }
        
        // Atualizar métricas a cada 30 segundos
        updateMetrics();
        setInterval(updateMetrics, 30000);
    </script>
</body>
</html>
"""
    
    os.makedirs("templates", exist_ok=True)
    with open("templates/monitor.html", "w", encoding="utf-8") as f:
        f.write(monitoring_html)

@app.route('/monitor')
def monitoring_dashboard():
    """Serve dashboard de monitoramento"""
    return app.send_static_file('monitor.html')

# =============================================================================
# INICIALIZAÇÃO E EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    print("🚀 Iniciando HydroAlert Cloud API...")
    print("📊 Banco de dados inicializado")
    print("🔗 Endpoints configurados")
    print("📡 Pronto para receber dados dos sensores")
    
    # Criar arquivos de deploy
    CloudConfig.create_dockerfile()
    CloudConfig.create_requirements()
    create_monitoring_dashboard()
    
    print("\n📋 Endpoints disponíveis:")
    print("  GET  /api/health - Verificação de saúde")
    print("  GET  /api/sensors - Lista sensores")
    print("  POST /api/sensors/<id>/data - Recebe dados de sensores")
    print("  GET  /api/readings/recent - Leituras recentes")
    print("  GET  /api/alerts - Alertas ativos")
    print("  GET  /api/dashboard/summary - Resumo do dashboard")
    print("  GET  /monitor - Dashboard de monitoramento")
    
    # Executar aplicação
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        debug=False
    )
