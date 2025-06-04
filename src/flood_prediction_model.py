import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time
import json
import os
import matplotlib.pyplot as plt
import tensorflow as tf
from scipy.interpolate import interp1d

class FloodMonitoringSystem:
    def __init__(self, model_path='flood_prediction_model.h5', data_dir='data'):
        """
        Inicializa o sistema de monitoramento de inundações
        
        Args:
            model_path: Caminho para o modelo de ML treinado
            data_dir: Diretório para armazenar dados coletados
        """
        self.data_dir = data_dir
        self.locations = {}
        
        # Criar diretório de dados se não existir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Carregar modelo
        try:
            print("Carregando modelo de previsão...")
            self.model = tf.keras.models.load_model(model_path)
            print("Modelo carregado com sucesso!")
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            self.model = None
    
    def register_location(self, location_id, name, lat, lon, threshold=0.7):
        """Registra uma nova localização para monitoramento"""
        self.locations[location_id] = {
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'risk_threshold': threshold,
            'sensor_data': []
        }
        print(f"Localização registrada: {name} (ID: {location_id})")
    
    def process_sensor_data(self, location_id, data):
        """
        Processa dados recebidos dos sensores ESP32
        
        Args:
            location_id: ID da localização
            data: Dicionário com leituras dos sensores
        """
        if location_id not in self.locations:
            print(f"Erro: Localização {location_id} não registrada")
            return
        
        # Adicionar timestamp
        data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Adicionar aos dados da localização
        self.locations[location_id]['sensor_data'].append(data)
        
        # Salvar dados em CSV
        self._save_sensor_data(location_id)
        
        # Calcular risco atual
        risk_level = self.calculate_risk(location_id)
        
        print(f"Dados processados para {self.locations[location_id]['name']}")
        print(f"Leitura atual: Nível de água = {data.get('water_level', 'N/A')}cm, "
              f"Chuva = {data.get('rainfall', 'N/A')}mm, "
              f"Umidade = {data.get('soil_moisture', 'N/A')}%")
        print(f"Nível de risco calculado: {risk_level:.2f}")
        
        # Verificar se ultrapassou limiar de alerta
        if risk_level > self.locations[location_id]['risk_threshold']:
            self._trigger_alert(location_id, risk_level)
    
    def calculate_risk(self, location_id):
        """
        Calcula o risco atual de inundação usando o modelo ML
        
        Returns:
            Nível de risco entre 0 e 1
        """
        if not self.model or location_id not in self.locations:
            return 0.5  # Valor padrão se não puder calcular
        
        # Obter dados históricos dos últimos 7 dias
        data = self.locations[location_id]['sensor_data']
        if len(data) < 7:
            # Se não tivermos dados suficientes, não podemos prever corretamente
            return 0.5
        
        # Usar os 7 dias mais recentes
        recent_data = data[-7:]
        
        # Extrair características
        rainfall = [d.get('rainfall', 0) for d in recent_data]
        water_level = [d.get('water_level', 0) for d in recent_data]
        moisture = [d.get('soil_moisture', 0) for d in recent_data]
        
        # Preparar entrada para o modelo
        X = np.array([rainfall, water_level, moisture]).T
        X = X.reshape(1, X.shape[0], X.shape[1])  # Formato: [1, time_steps, features]
        
        # Fazer previsão
        try:
            risk = float(self.model.predict(X, verbose=0)[0][0])
            return risk
        except Exception as e:
            print(f"Erro ao prever risco: {e}")
            return 0.5
    
    def _save_sensor_data(self, location_id):
        """Salva dados dos sensores em arquivo CSV"""
        location_name = self.locations[location_id]['name']
        filename = os.path.join(self.data_dir, f"{location_id}_sensor_data.csv")
        
        df = pd.DataFrame(self.locations[location_id]['sensor_data'])
        df.to_csv(filename, index=False)
    
    def _trigger_alert(self, location_id, risk_level):
        """Dispara um alerta quando o risco ultrapassa o limiar"""
        location = self.locations[location_id]
        print("\n" + "!"*50)
        print(f"ALERTA DE INUNDAÇÃO: {location['name']}")
        print(f"Risco atual: {risk_level:.2f}")
        print(f"Coordenadas: {location['latitude']}, {location['longitude']}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("!"*50 + "\n")
        
        # Aqui você pode adicionar código para enviar notificações:
        # - SMS usando Twilio
        # - E-mail
        # - Push notifications
        # - Integração com serviços de emergência
    
    def visualize_data(self, location_id):
        """Visualiza dados históricos de uma localização"""
        if location_id not in self.locations:
            print(f"Erro: Localização {location_id} não encontrada")
            return
        
        data = self.locations[location_id]['sensor_data']
        if not data:
            print("Sem dados para visualizar")
            return
        
        df = pd.DataFrame(data)
        
        # Converter timestamp para datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Plotar gráficos
        fig, ax = plt.subplots(3, 1, figsize=(12, 10))
        
        ax[0].plot(df['timestamp'], df['rainfall'], 'b-')
        ax[0].set_title('Precipitação (mm)')
        ax[0].grid(True)
        
        ax[1].plot(df['timestamp'], df['water_level'], 'r-')
        ax[1].set_title('Nível de Água (cm)')
        ax[1].grid(True)
        
        ax[2].plot(df['timestamp'], df['soil_moisture'], 'g-')
        ax[2].set_title('Umidade do Solo (%)')
        ax[2].grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.data_dir, f"{location_id}_visualization.png"))
        plt.close()
        
        print(f"Visualização salva em {self.data_dir}/{location_id}_visualization.png")
    
    def simulate_sensor_data(self, location_id, days=30, interval_hours=1):
        """
        Simula dados de sensores para teste
        
        Args:
            location_id: ID da localização
            days: Número de dias a simular
            interval_hours: Intervalo entre leituras em horas
        """
        if location_id not in self.locations:
            print(f"Erro: Localização {location_id} não encontrada")
            return
        
        print(f"Simulando {days} dias de dados para {self.locations[location_id]['name']}...")
        
        # Limpar dados existentes
        self.locations[location_id]['sensor_data'] = []
        
        # Gerar dados simulados
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        current_time = start_time
        time_points = []
        
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(hours=interval_hours)
        
        # Simular tendência sazonal de chuva (mais chuva no verão)
        base_rainfall = 5  # mm por hora em média
        rainfall_data = []
        
        for t in time_points:
            # Fator sazonal (maior em dezembro-março)
            month = t.month
            seasonal_factor = 2.0 if month in [12, 1, 2, 3] else 1.0
            
            # Adicionar alguma aleatoriedade
            random_factor = np.random.normal(1, 0.5)
            
            # Possibilidade de evento de chuva intensa
            intense_rain = 3.0 if np.random.random() < 0.05 else 1.0
            
            rainfall = base_rainfall * seasonal_factor * random_factor * intense_rain
            rainfall = max(0, rainfall)  # Não pode ser negativo
            
            rainfall_data.append(rainfall)
        
        # O nível de água e umidade do solo seguem a tendência da chuva, com algum atraso
        water_level_data = []
        moisture_data = []
        
        # Base values
        base_water_level = 40  # cm
        base_moisture = 60  # %
        
        # Criar efeitos cumulativos e de atraso
        for i, rainfall in enumerate(rainfall_data):
            # O nível de água responde à chuva com algum atraso
            if i < 24:  # Primeiras 24h
                water_level = base_water_level + (rainfall * 2)
            else:
                # Efeito cumulativo das últimas 24 horas de chuva
                recent_rainfall = sum(rainfall_data[i-24:i])
                water_level = base_water_level + (recent_rainfall * 0.5)
            
            # Garantir limites razoáveis
            water_level = min(120, max(20, water_level))
            
            # A umidade do solo também responde à chuva, mas com menos sensibilidade
            if i < 12:
                moisture = base_moisture + (rainfall * 1.5)
            else:
                recent_rainfall = sum(rainfall_data[i-12:i])
                moisture = base_moisture + (recent_rainfall * 0.3)
            
            # Garantir limites razoáveis (0-100%)
            moisture = min(98, max(30, moisture))
            
            water_level_data.append(water_level)
            moisture_data.append(moisture)
        
        # Criar eventos de dados
        for i, t in enumerate(time_points):
            data = {
                'timestamp': t.strftime("%Y-%m-%d %H:%M:%S"),
                'rainfall': rainfall_data[i],
                'water_level': water_level_data[i],
                'soil_moisture': moisture_data[i]
            }
            
            self.locations[location_id]['sensor_data'].append(data)
        
        # Salvar dados simulados
        self._save_sensor_data(location_id)
        print(f"Simulação concluída: {len(time_points)} pontos de dados gerados")

# Exemplo de uso
if __name__ == "__main__":
    # Inicializar sistema
    system = FloodMonitoringSystem()
    
    # Registrar localizações
    system.register_location('SP001', 'São Paulo - Zona Norte', -23.5, -46.63)
    system.register_location('RJ001', 'Rio de Janeiro - Maracanã', -22.91, -43.23)
    system.register_location('BL001', 'Blumenau - Centro', -26.91, -49.06)
    
    # Simular dados históricos
    system.simulate_sensor_data('SP001', days=30)
    system.simulate_sensor_data('RJ001', days=30)
    system.simulate_sensor_data('BL001', days=30)
    
    # Visualizar dados
    system.visualize_data('SP001')
    
    # Simular dado de sensor em tempo real
    real_time_data = {
        'rainfall': 25.3,       # Chuva intensa
        'water_level': 82.7,    # Nível alto de água
        'soil_moisture': 95.2   # Solo saturado
    }
    
    # Processar dado e verificar alerta
    system.process_sensor_data('SP001', real_time_data)
    
    print("\nSistema de monitoramento iniciado com sucesso!")
    print("Para integrar com o ESP32, configure o dispositivo para enviar")
    print("dados para este sistema através de uma API REST.")