"""
Sistema de Banco de Dados para HydroAlert
Global Solution 2025.1 - FIAP
Grupo 35 - Componente de Banco de Dados

Implementa sistema completo de armazenamento com:
- SQLite para desenvolvimento local
- Estrutura preparada para PostgreSQL/MySQL em produção
- Operações CRUD completas
- Consultas otimizadas para análises
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Sensor:
    """Estrutura de dados para sensores"""
    id: str
    name: str
    latitude: float
    longitude: float
    installation_date: str
    status: str = "active"
    sensor_type: str = "water_level"
    calibration_date: Optional[str] = None

@dataclass
class SensorReading:
    """Estrutura de dados para leituras de sensores"""
    sensor_id: str
    timestamp: str
    rainfall: float
    water_level: float
    soil_moisture: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    battery_level: Optional[float] = None

@dataclass
class FloodPrediction:
    """Estrutura de dados para previsões"""
    sensor_id: str
    prediction_timestamp: str
    target_timestamp: str
    flood_probability: float
    risk_level: str
    confidence_score: float
    model_version: str = "v1.0"

@dataclass
class Alert:
    """Estrutura de dados para alertas"""
    sensor_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None

class HydroAlertDatabase:
    """
    Classe principal para gerenciamento do banco de dados HydroAlert
    """
    
    def __init__(self, db_path: str = "data/hydroalert.db"):
        """
        Inicializa conexão com banco de dados
        
        Args:
            db_path: Caminho para arquivo SQLite
        """
        self.db_path = db_path
        self.ensure_data_directory()
        self.init_database()
        self.insert_sample_data()
    
    def ensure_data_directory(self):
        """Garante que o diretório de dados existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Cria conexão com banco de dados
        
        Returns:
            Conexão SQLite
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        return conn
    
    def init_database(self):
        """
        Inicializa estrutura do banco de dados
        """
        logger.info("Inicializando estrutura do banco de dados...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de sensores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                installation_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                sensor_type TEXT DEFAULT 'water_level',
                calibration_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de leituras dos sensores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                rainfall REAL NOT NULL,
                water_level REAL NOT NULL,
                soil_moisture REAL NOT NULL,
                temperature REAL,
                humidity REAL,
                battery_level REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES sensors (id),
                UNIQUE(sensor_id, timestamp)
            )
        """)
        
        # Tabela de previsões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flood_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                prediction_timestamp TEXT NOT NULL,
                target_timestamp TEXT NOT NULL,
                flood_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                confidence_score REAL NOT NULL,
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
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by TEXT,
                acknowledged_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES sensors (id)
            )
        """)
        
        # Tabela de histórico de manutenção
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                maintenance_type TEXT NOT NULL,
                description TEXT,
                performed_by TEXT NOT NULL,
                performed_at TEXT NOT NULL,
                next_maintenance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES sensors (id)
            )
        """)
        
        # Tabela de configurações do sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Criar índices para otimização
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_sensor_time ON sensor_readings(sensor_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_sensor_time ON flood_predictions(sensor_id, prediction_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Estrutura do banco de dados criada com sucesso")
    
    def insert_sample_data(self):
        """
        Insere dados de exemplo no banco
        """
        logger.info("Inserindo dados de exemplo...")
        
        # Sensores de exemplo
        sample_sensors = [
            Sensor("SP001", "São Paulo - Zona Norte", -23.5, -46.63, "2025-01-01", "active"),
            Sensor("RJ001", "Rio de Janeiro - Maracanã", -22.91, -43.23, "2025-01-02", "active"),
            Sensor("BL001", "Blumenau - Centro", -26.91, -49.06, "2025-01-03", "active"),
            Sensor("PE001", "Recife - Boa Viagem", -8.12, -34.90, "2025-01-04", "active"),
            Sensor("RS001", "Porto Alegre - Sarandi", -30.03, -51.18, "2025-01-05", "active")
        ]
        
        for sensor in sample_sensors:
            self.insert_sensor(sensor)
        
        # Configurações padrão do sistema
        default_configs = [
            ("flood_threshold", "0.7", "Threshold de probabilidade para alerta de inundação"),
            ("alert_retention_days", "30", "Dias para manter alertas no sistema"),
            ("reading_frequency_minutes", "30", "Frequência de leitura dos sensores em minutos"),
            ("model_version", "v1.0", "Versão atual do modelo de ML"),
            ("system_status", "operational", "Status operacional do sistema")
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for key, value, description in default_configs:
            cursor.execute("""
                INSERT OR IGNORE INTO system_config (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Dados de exemplo inseridos com sucesso")
    
    # ==========================================================================
    # OPERAÇÕES CRUD - SENSORES
    # ==========================================================================
    
    def insert_sensor(self, sensor: Sensor) -> bool:
        """
        Insere novo sensor no banco
        
        Args:
            sensor: Objeto Sensor a ser inserido
            
        Returns:
            True se inserido com sucesso, False caso contrário
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sensors 
                (id, name, latitude, longitude, installation_date, status, sensor_type, calibration_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sensor.id, sensor.name, sensor.latitude, sensor.longitude,
                  sensor.installation_date, sensor.status, sensor.sensor_type, sensor.calibration_date))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Sensor {sensor.id} inserido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir sensor: {e}")
            return False
    
    def get_sensor(self, sensor_id: str) -> Optional[Dict]:
        """
        Recupera sensor por ID
        
        Args:
            sensor_id: ID do sensor
            
        Returns:
            Dicionário com dados do sensor ou None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sensors WHERE id = ?", (sensor_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_sensors(self, status: str = None) -> List[Dict]:
        """
        Recupera todos os sensores
        
        Args:
            status: Filtrar por status (opcional)
            
        Returns:
            Lista de sensores
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM sensors WHERE status = ? ORDER BY name", (status,))
        else:
            cursor.execute("SELECT * FROM sensors ORDER BY name")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==========================================================================
    # OPERAÇÕES CRUD - LEITURAS DE SENSORES
    # ==========================================================================
    
    def insert_reading(self, reading: SensorReading) -> bool:
        """
        Insere nova leitura de sensor
        
        Args:
            reading: Objeto SensorReading
            
        Returns:
            True se inserido com sucesso
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sensor_readings 
                (sensor_id, timestamp, rainfall, water_level, soil_moisture, 
                 temperature, humidity, battery_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (reading.sensor_id, reading.timestamp, reading.rainfall,
                  reading.water_level, reading.soil_moisture, reading.temperature,
                  reading.humidity, reading.battery_level))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir leitura: {e}")
            return False
    
    def get_readings(self, sensor_id: str = None, start_date: str = None, 
                    end_date: str = None, limit: int = 1000) -> pd.DataFrame:
        """
        Recupera leituras dos sensores
        
        Args:
            sensor_id: ID do sensor (opcional)
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            limit: Limite de registros
            
        Returns:
            DataFrame com as leituras
        """
        conn = self.get_connection()
        
        query = """
            SELECT r.*, s.name as sensor_name, s.latitude, s.longitude
            FROM sensor_readings r
            JOIN sensors s ON r.sensor_id = s.id
            WHERE 1=1
        """
        params = []
        
        if sensor_id:
            query += " AND r.sensor_id = ?"
            params.append(sensor_id)
        
        if start_date:
            query += " AND r.timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND r.timestamp <= ?"
            params.append(end_date)
        
        query += f" ORDER BY r.timestamp DESC LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_latest_readings(self, hours: int = 24) -> pd.DataFrame:
        """
        Recupera leituras mais recentes
        
        Args:
            hours: Número de horas para buscar
            
        Returns:
            DataFrame com leituras recentes
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        return self.get_readings(start_date=cutoff_time)
    
    # ==========================================================================
    # OPERAÇÕES CRUD - PREVISÕES
    # ==========================================================================
    
    def insert_prediction(self, prediction: FloodPrediction) -> bool:
        """
        Insere nova previsão
        
        Args:
            prediction: Objeto FloodPrediction
            
        Returns:
            True se inserido com sucesso
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO flood_predictions 
                (sensor_id, prediction_timestamp, target_timestamp, flood_probability,
                 risk_level, confidence_score, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (prediction.sensor_id, prediction.prediction_timestamp,
                  prediction.target_timestamp, prediction.flood_probability,
                  prediction.risk_level, prediction.confidence_score, prediction.model_version))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir previsão: {e}")
            return False
    
    def get_latest_predictions(self, sensor_id: str = None, hours: int = 24) -> pd.DataFrame:
        """
        Recupera previsões mais recentes
        
        Args:
            sensor_id: ID do sensor (opcional)
            hours: Horas para buscar
            
        Returns:
            DataFrame com previsões
        """
        conn = self.get_connection()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        query = """
            SELECT p.*, s.name as sensor_name
            FROM flood_predictions p
            JOIN sensors s ON p.sensor_id = s.id
            WHERE p.prediction_timestamp >= ?
        """
        params = [cutoff_time]
        
        if sensor_id:
            query += " AND p.sensor_id = ?"
            params.append(sensor_id)
        
        query += " ORDER BY p.prediction_timestamp DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    # ==========================================================================
    # OPERAÇÕES CRUD - ALERTAS
    # ==========================================================================
    
    def insert_alert(self, alert: Alert) -> bool:
        """
        Insere novo alerta
        
        Args:
            alert: Objeto Alert
            
        Returns:
            True se inserido com sucesso
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alerts 
                (sensor_id, alert_type, severity, message, timestamp, acknowledged,
                 acknowledged_by, acknowledged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (alert.sensor_id, alert.alert_type, alert.severity, alert.message,
                  alert.timestamp, alert.acknowledged, alert.acknowledged_by, alert.acknowledged_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🚨 Alerta criado: {alert.alert_type} - {alert.severity}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir alerta: {e}")
            return False
    
    def get_active_alerts(self) -> pd.DataFrame:
        """
        Recupera alertas ativos (não reconhecidos)
        
        Returns:
            DataFrame com alertas ativos
        """
        conn = self.get_connection()
        
        query = """
            SELECT a.*, s.name as sensor_name, s.latitude, s.longitude
            FROM alerts a
            JOIN sensors s ON a.sensor_id = s.id
            WHERE a.acknowledged = FALSE
            ORDER BY a.timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """
        Reconhece um alerta
        
        Args:
            alert_id: ID do alerta
            acknowledged_by: Usuário que reconheceu
            
        Returns:
            True se reconhecido com sucesso
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE alerts 
                SET acknowledged = TRUE, acknowledged_by = ?, acknowledged_at = ?
                WHERE id = ?
            """, (acknowledged_by, datetime.now().isoformat(), alert_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Alerta {alert_id} reconhecido por {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao reconhecer alerta: {e}")
            return False
    
    # ==========================================================================
    # CONSULTAS ANALÍTICAS
    # ==========================================================================
    
    def get_sensor_statistics(self, sensor_id: str, days: int = 30) -> Dict:
        """
        Calcula estatísticas de um sensor
        
        Args:
            sensor_id: ID do sensor
            days: Número de dias para análise
            
        Returns:
            Dicionário com estatísticas
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        df = self.get_readings(sensor_id=sensor_id, start_date=cutoff_date)
        
        if df.empty:
            return {}
        
        stats = {
            "total_readings": len(df),
            "period_days": days,
            "rainfall": {
                "mean": float(df['rainfall'].mean()),
                "max": float(df['rainfall'].max()),
                "min": float(df['rainfall'].min()),
                "std": float(df['rainfall'].std())
            },
            "water_level": {
                "mean": float(df['water_level'].mean()),
                "max": float(df['water_level'].max()),
                "min": float(df['water_level'].min()),
                "std": float(df['water_level'].std())
            },
            "soil_moisture": {
                "mean": float(df['soil_moisture'].mean()),
                "max": float(df['soil_moisture'].max()),
                "min": float(df['soil_moisture'].min()),
                "std": float(df['soil_moisture'].std())
            }
        }
        
        return stats
    
    def get_system_summary(self) -> Dict:
        """
        Retorna resumo geral do sistema
        
        Returns:
            Dicionário com resumo
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total de sensores
        cursor.execute("SELECT COUNT(*) FROM sensors WHERE status = 'active'")
        total_sensors = cursor.fetchone()[0]
        
        # Alertas ativos
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = FALSE")
        active_alerts = cursor.fetchone()[0]
        
        # Leituras nas últimas 24h
        cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE timestamp >= ?", (cutoff_time,))
        readings_24h = cursor.fetchone()[0]
        
        # Previsões de alto risco
        cursor.execute("""
            SELECT COUNT(*) FROM flood_predictions 
            WHERE risk_level IN ('ALTO', 'CRÍTICO') 
            AND prediction_timestamp >= ?
        """, (cutoff_time,))
        high_risk_predictions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_sensors": total_sensors,
            "active_alerts": active_alerts,
            "readings_24h": readings_24h,
            "high_risk_predictions": high_risk_predictions,
            "last_updated": datetime.now().isoformat()
        }
    
    def export_data_to_csv(self, table_name: str, output_path: str, 
                          start_date: str = None, end_date: str = None) -> bool:
        """
        Exporta dados para CSV
        
        Args:
            table_name: Nome da tabela
            output_path: Caminho do arquivo de saída
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            True se exportado com sucesso
        """
        try:
            conn = self.get_connection()
            
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if table_name == "sensor_readings" and (start_date or end_date):
                query += " WHERE 1=1"
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
            
            df = pd.read_sql_query(query, conn, params=params)
            df.to_csv(output_path, index=False)
            
            conn.close()
            
            logger.info(f"✅ Dados exportados para: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar dados: {e}")
            return False

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def create_sample_readings(db: HydroAlertDatabase, sensor_id: str, days: int = 7):
    """
    Cria leituras de exemplo para um sensor
    
    Args:
        db: Instância do banco de dados
        sensor_id: ID do sensor
        days: Número de dias de dados
    """
    logger.info(f"Criando {days} dias de dados para sensor {sensor_id}")
    
    start_time = datetime.now() - timedelta(days=days)
    
    for i in range(days * 48):  # 48 leituras por dia (a cada 30 min)
        timestamp = start_time + timedelta(minutes=30 * i)
        
        # Simular dados realistas
        base_rainfall = max(0, np.random.normal(5, 8))
        base_water = max(40, np.random.normal(60, 20))
        base_moisture = max(60, min(100, np.random.normal(75, 15)))
        
        reading = SensorReading(
            sensor_id=sensor_id,
            timestamp=timestamp.isoformat(),
            rainfall=round(base_rainfall, 2),
            water_level=round(base_water, 2),
            soil_moisture=round(base_moisture, 2),
            temperature=round(np.random.normal(25, 5), 1),
            humidity=round(np.random.normal(70, 15), 1),
            battery_level=round(np.random.normal(85, 10), 1)
        )
        
        db.insert_reading(reading)

# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    print("🗄️ Inicializando Sistema de Banco de Dados HydroAlert")
    
    # Criar instância do banco
    db = HydroAlertDatabase()
    
    # Criar dados de exemplo
    for sensor_id in ["SP001", "RJ001", "BL001"]:
        create_sample_readings(db, sensor_id, days=7)
    
    # Teste de operações
    print("\n📊 Resumo do Sistema:")
    summary = db.get_system_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n📈 Estatísticas do Sensor SP001:")
    stats = db.get_sensor_statistics("SP001")
    if stats:
        print(f"  Total de leituras: {stats['total_readings']}")
        print(f"  Precipitação média: {stats['rainfall']['mean']:.2f} mm")
        print(f"  Nível de água médio: {stats['water_level']['mean']:.2f} cm")
    
    print("\n✅ Sistema de Banco de Dados configurado com sucesso!")
    print(f"📁 Banco de dados: {db.db_path}")
    print("🔗 Pronto para integração com outros componentes")
