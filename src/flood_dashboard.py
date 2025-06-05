import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import tensorflow as tf
from datetime import datetime, timedelta
import json
import os

# Criar diretório de dados se não existir
data_dir = 'data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Carregar modelo treinado
@st.cache_resource
def load_model():
    try:
        model = tf.keras.models.load_model('flood_prediction_model.h5')
        return model
    except:
        st.error("Modelo não encontrado. Execute primeiro o script de treinamento.")
        return None

# Simula dados de sensores em diferentes localizações
@st.cache_data
def generate_sensor_data():
    # Localizações fictícias (coordenadas de algumas cidades brasileiras sujeitas a inundações)
    locations = {
        "São Paulo - Zona Norte": {"lat": -23.5, "lon": -46.63, "rainfall": 12.3, "water_level": 75, "moisture": 82},
        "Rio de Janeiro - Maracanã": {"lat": -22.91, "lon": -43.23, "rainfall": 15.7, "water_level": 85, "moisture": 89},
        "Blumenau - Centro": {"lat": -26.91, "lon": -49.06, "rainfall": 18.2, "water_level": 92, "moisture": 93},
        "Recife - Boa Viagem": {"lat": -8.12, "lon": -34.90, "rainfall": 10.5, "water_level": 65, "moisture": 78},
        "Porto Alegre - Sarandi": {"lat": -30.03, "lon": -51.18, "rainfall": 16.8, "water_level": 88, "moisture": 90}
    }
    
    # Adiciona dados históricos dos últimos 7 dias para cada local
    for loc in locations:
        # Gera dados históricos fictícios de chuva com tendência crescente
        rainfall_history = []
        water_level_history = []
        moisture_history = []
        
        base_rainfall = locations[loc]["rainfall"] * 0.6
        base_water = locations[loc]["water_level"] * 0.7
        base_moisture = locations[loc]["moisture"] * 0.8

        # Forçar valores extremos para Blumenau - Centro para testar o risco
        if loc == "Blumenau - Centro":
            for i in range(7):
                # Simula chuva extrema, nível de água alto e solo saturado
                rainfall_history.append(50 + np.random.normal(0, 2))
                water_level_history.append(120 + np.random.normal(0, 4))
                moisture_history.append(98 + np.random.normal(0, 1))
        else:
            for i in range(7):
                factor = 0.7 + (i * 0.05)  # Aumenta gradualmente
                rainfall_history.append(base_rainfall * factor + np.random.normal(0, 2))
                water_level_history.append(base_water * factor + np.random.normal(0, 4))
                moisture_history.append(min(100, base_moisture * factor + np.random.normal(0, 3)))
        
        locations[loc]["rainfall_history"] = rainfall_history
        locations[loc]["water_level_history"] = water_level_history
        locations[loc]["moisture_history"] = moisture_history
        
    return locations

def predict_risk_level(model, location_data):
    """Calcula risco com base no histórico de 7 dias"""
    if not model:
        return 0.5  # Valor padrão se o modelo não estiver disponível
        
    # Prepara dados de entrada para o modelo
    features = np.array([
        location_data["rainfall_history"],
        location_data["water_level_history"],
        location_data["moisture_history"]
    ]).T  # Transposição para formato [7 dias, 3 features]
    
    # Reshape para formato esperado pelo LSTM [1, time_steps, features]
    input_data = features.reshape(1, features.shape[0], features.shape[1])
    
    # Faz a previsão
    risk = float(model.predict(input_data, verbose=0)[0][0])
    return risk

def get_risk_color(risk):
    """Retorna cor baseada no nível de risco"""
    if risk < 0.3:
        return "green"
    elif risk < 0.7:
        return "orange"
    else:
        return "red"

def get_risk_text(risk):
    """Retorna texto baseado no nível de risco"""
    if risk < 0.3:
        return "Baixo"
    elif risk < 0.7:
        return "Médio"
    else:
        return "Alto"

# Interface do dashboard
st.set_page_config(page_title="Sistema de Alerta de Inundações", layout="wide")

st.title("🌊 Sistema de Monitoramento e Alerta de Inundações")
st.markdown("### Monitoramento em Tempo Real e Previsão de Riscos")

# Carregar modelo e dados
model = load_model()
sensor_data = generate_sensor_data()

# Adicionar data e hora atual
current_time = datetime.now()
st.sidebar.write(f"**Última atualização:**  \n{current_time.strftime('%d/%m/%Y %H:%M:%S')}")

# Adicionar filtro de região
selected_region = st.sidebar.selectbox(
    "Selecionar região de monitoramento",
    list(sensor_data.keys())
)

# Calcular risco para a região selecionada
risk_level = predict_risk_level(model, sensor_data[selected_region])

# Layout de duas colunas
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Mapa de Risco - {selected_region}")
    
    # Criar mapa
    m = folium.Map(
        location=[sensor_data[selected_region]["lat"], sensor_data[selected_region]["lon"]], 
        zoom_start=12
    )
    
    # Adicionar marcador para o local selecionado
    folium.Marker(
        [sensor_data[selected_region]["lat"], sensor_data[selected_region]["lon"]],
        popup=f"{selected_region}<br>Risco: {get_risk_text(risk_level)}",
        icon=folium.Icon(color=get_risk_color(risk_level))
    ).add_to(m)
    
    # Adicionar marcadores para todos os locais
    for loc in sensor_data:
        if loc != selected_region:
            loc_risk = predict_risk_level(model, sensor_data[loc])
            folium.CircleMarker(
                [sensor_data[loc]["lat"], sensor_data[loc]["lon"]],
                radius=8,
                popup=f"{loc}<br>Risco: {get_risk_text(loc_risk)}",
                fill=True,
                fill_color=get_risk_color(loc_risk),
                color=get_risk_color(loc_risk)
            ).add_to(m)
    
    # Exibir mapa
    folium_static(m)
    
    # Gráficos históricos
    st.subheader("Histórico dos Últimos 7 Dias")
    
    dates = [(current_time - timedelta(days=6-i)).strftime("%d/%m") for i in range(7)]
    
    fig, ax = plt.subplots(3, 1, figsize=(10, 8))
    
    ax[0].plot(dates, sensor_data[selected_region]["rainfall_history"], 'b-o')
    ax[0].set_title('Precipitação (mm)')
    ax[0].grid(True)
    
    ax[1].plot(dates, sensor_data[selected_region]["water_level_history"], 'r-o')
    ax[1].set_title('Nível de Água (cm)')
    ax[1].grid(True)
    
    ax[2].plot(dates, sensor_data[selected_region]["moisture_history"], 'g-o')
    ax[2].set_title('Umidade do Solo (%)')
    ax[2].set_ylim([0, 100])
    ax[2].grid(True)
    
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("Indicador de Risco")
    
    # Mostrar medidor de risco
    st.markdown(
        f"""
        <div style="text-align: center;">
            <div style="margin: 0 auto; width: 200px; height: 200px; border-radius: 50%; 
                background: conic-gradient(
                    red {int(risk_level * 360)}deg, 
                    #f0f0f0 {int(risk_level * 360)}deg 360deg
                );">
                <div style="position: relative; top: 10px; left: 10px; width: 180px; height: 180px; 
                         border-radius: 50%; background: white; display: flex; 
                         align-items: center; justify-content: center; text-align: center;">
                    <div>
                        <h2 style="margin:0; color: {get_risk_color(risk_level)};">{int(risk_level * 100)}%</h2>
                        <p style="margin:0; font-size: 1.2em;">Risco de<br>Inundação</p>
                    </div>
                </div>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Status atual dos sensores
    st.subheader("Leituras Atuais dos Sensores")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.metric("Precipitação", f"{sensor_data[selected_region]['rainfall']:.1f} mm")
        st.metric("Umidade do Solo", f"{sensor_data[selected_region]['moisture']:.1f}%")
    
    with col_b:
        st.metric("Nível de Água", f"{sensor_data[selected_region]['water_level']:.1f} cm")
        
    # Recomendações baseadas no risco
    st.subheader("Recomendações")
    
    if risk_level < 0.3:
        st.success("✅ Risco baixo. Mantenha monitoramento normal.")
    elif risk_level < 0.7:
        st.warning("""
        ⚠️ Risco moderado. Recomendações:
        - Monitorar boletins meteorológicos
        - Verificar sistemas de drenagem
        - Alertar equipes de emergência
        """)
    else:
        st.error("""
        🚨 ALERTA DE ALTO RISCO! Ações urgentes:
        - Mobilizar equipes de emergência
        - Considerar evacuação preventiva de áreas críticas
        - Ativar protocolos de emergência
        - Comunicar autoridades locais
        """)
    
    # Histórico de alertas
    st.subheader("Histórico de Alertas")
    
    # Simula alguns alertas
    alerts = [
        {"timestamp": "03/06/2025 09:15", "level": "Alto", "message": "Nível de água ultrapassou limite crítico"},
        {"timestamp": "02/06/2025 23:30", "level": "Médio", "message": "Precipitação intensa nas últimas 3 horas"},
        {"timestamp": "01/06/2025 14:45", "level": "Baixo", "message": "Umidade do solo elevada"}
    ]
    
    for alert in alerts:
        color = "red" if alert["level"] == "Alto" else "orange" if alert["level"] == "Médio" else "green"
        st.markdown(f"""
        <div style="border-left: 4px solid {color}; padding-left: 10px; margin-bottom: 10px;">
            <p style="margin: 0; color: gray; font-size: 0.8em;">{alert['timestamp']}</p>
            <p style="margin: 0; font-weight: bold; color: {color};">{alert['level']}</p>
            <p style="margin: 0;">{alert['message']}</p>
        </div>
        """, unsafe_allow_html=True)

# Rodapé
st.markdown("---")
st.markdown("**Sistema de Alerta de Inundações** | Global Solution 2025.1 | FIAP")

# Instruções para executar
if __name__ == "__main__":
    st.sidebar.markdown("""
    ## Como executar
    ```
    streamlit run flood_dashboard.py
    ```
    """)