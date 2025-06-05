import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
import tensorflow as tf
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Sistema de Alerta de Inundações", layout="wide")


@st.cache_resource
def load_model():
    try:
        model = tf.keras.models.load_model("flood_prediction_model.h5")
        return model
    except:
        st.error("Modelo não encontrado. Execute primeiro o script de treinamento.")
        return None


@st.cache_data(ttl=60)
def fetch_sensor_data_from_api():
    try:
        url = "http://localhost:8080/api/readings/recent"
        response = requests.get(url)
        response.raise_for_status()
        raw_data = response.json()["readings"]

        locations = {}
        for entry in raw_data:
            loc = entry["name"]
            if loc not in locations:
                locations[loc] = {
                    "lat": entry["latitude"],
                    "lon": entry["longitude"],
                    "rainfall_history": [],
                    "water_level_history": [],
                    "moisture_history": [],
                }

            locations[loc]["rainfall_history"].append(
                (entry["timestamp"], entry["rainfall"])
            )
            locations[loc]["water_level_history"].append(
                (entry["timestamp"], entry["water_level"])
            )
            locations[loc]["moisture_history"].append(
                (entry["timestamp"], entry["soil_moisture"])
            )

        for loc in locations:
            for key in ["rainfall_history", "water_level_history", "moisture_history"]:
                # Ordenar por timestamp e pegar os últimos 7
                locations[loc][key] = [v for t, v in sorted(locations[loc][key])[-7:]]
            locations[loc]["rainfall"] = locations[loc]["rainfall_history"][-1]
            locations[loc]["water_level"] = locations[loc]["water_level_history"][-1]
            locations[loc]["moisture"] = locations[loc]["moisture_history"][-1]

        return locations
    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")
        return {}


def predict_risk_level(model, location_data):
    if not model:
        return 0.5
    features = np.array(
        [
            location_data["rainfall_history"],
            location_data["water_level_history"],
            location_data["moisture_history"],
        ]
    ).T
    input_data = features.reshape(1, features.shape[0], features.shape[1])
    risk = float(model.predict(input_data, verbose=0)[0][0])
    return risk


def get_risk_color(risk):
    if risk < 0.3:
        return "green"
    elif risk < 0.7:
        return "orange"
    else:
        return "red"


def get_risk_text(risk):
    if risk < 0.3:
        return "Baixo"
    elif risk < 0.7:
        return "Médio"
    else:
        return "Alto"


# Interface
st.title("🌊 Sistema de Monitoramento e Alerta de Inundações")
st.markdown("### Monitoramento em Tempo Real e Previsão de Riscos")

model = load_model()
sensor_data = fetch_sensor_data_from_api()
current_time = datetime.now()
st.sidebar.write(
    f"**Última atualização:**  \n{current_time.strftime('%d/%m/%Y %H:%M:%S')}"
)

if not sensor_data:
    st.warning("Nenhum dado disponível no momento.")
    st.stop()

selected_region = st.sidebar.selectbox(
    "Selecionar região de monitoramento", list(sensor_data.keys())
)
risk_level = predict_risk_level(model, sensor_data[selected_region])
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Mapa de Risco - {selected_region}")
    m = folium.Map(
        location=[
            sensor_data[selected_region]["lat"],
            sensor_data[selected_region]["lon"],
        ],
        zoom_start=12,
    )
    folium.Marker(
        [sensor_data[selected_region]["lat"], sensor_data[selected_region]["lon"]],
        popup=f"{selected_region}<br>Risco: {get_risk_text(risk_level)}",
        icon=folium.Icon(color=get_risk_color(risk_level)),
    ).add_to(m)

    for loc in sensor_data:
        if loc != selected_region:
            loc_risk = predict_risk_level(model, sensor_data[loc])
            folium.CircleMarker(
                [sensor_data[loc]["lat"], sensor_data[loc]["lon"]],
                radius=8,
                popup=f"{loc}<br>Risco: {get_risk_text(loc_risk)}",
                fill=True,
                fill_color=get_risk_color(loc_risk),
                color=get_risk_color(loc_risk),
            ).add_to(m)

    folium_static(m)

    st.subheader("Histórico dos Últimos Dias")
    history_len = len(sensor_data[selected_region]["rainfall_history"])
    if history_len < 2:
        st.warning("Histórico insuficiente para exibir os gráficos.")
    else:
        dates = [
            (current_time - timedelta(days=history_len - 1 - i)).strftime("%d/%m")
            for i in range(history_len)
        ]
        fig, ax = plt.subplots(3, 1, figsize=(10, 8))

        ax[0].plot(dates, sensor_data[selected_region]["rainfall_history"], "b-o")
        ax[0].set_title("Precipitação (mm)")
        ax[0].grid(True)

        ax[1].plot(dates, sensor_data[selected_region]["water_level_history"], "r-o")
        ax[1].set_title("Nível de Água (cm)")
        ax[1].grid(True)

        ax[2].plot(dates, sensor_data[selected_region]["moisture_history"], "g-o")
        ax[2].set_title("Umidade do Solo (%)")
        ax[2].set_ylim([0, 100])
        ax[2].grid(True)

        plt.tight_layout()
        st.pyplot(fig)

with col2:
    st.subheader("Indicador de Risco")
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
        unsafe_allow_html=True,
    )

    st.subheader("Leituras Atuais dos Sensores")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Precipitação", f"{sensor_data[selected_region]['rainfall']:.1f} mm")
        st.metric("Umidade do Solo", f"{sensor_data[selected_region]['moisture']:.1f}%")
    with col_b:
        st.metric(
            "Nível de Água", f"{sensor_data[selected_region]['water_level']:.1f} cm"
        )

    st.subheader("Recomendações")
    if risk_level < 0.3:
        st.success("✅ Risco baixo. Mantenha monitoramento normal.")
    elif risk_level < 0.7:
        st.warning("⚠️ Risco moderado. Monitorar condições e alertar equipes locais.")
    else:
        st.error("🚨 ALERTA CRÍTICO! Acionar protocolos de emergência imediatamente.")

st.markdown("---")
st.markdown("**Sistema de Alerta de Inundações** | Global Solution 2025.1 | FIAP")
