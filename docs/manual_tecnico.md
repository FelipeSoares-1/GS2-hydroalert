# Manual Técnico - Sistema de Previsão e Alerta de Inundações Urbanas

## Versão 1.0 - Global Solution 2025.1

---

## Sumário

1. [Introdução](#introdução)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Componentes Hardware](#componentes-hardware)
4. [Componentes Software](#componentes-software)
5. [Instalação e Configuração](#instalação-e-configuração)
6. [Operação do Sistema](#operação-do-sistema)
7. [Manutenção](#manutenção)
8. [Troubleshooting](#troubleshooting)

---

## 1. Introdução

Este manual descreve o sistema de previsão e alerta de inundações urbanas desenvolvido para a Global Solution 2025.1 da FIAP. O sistema combina sensores IoT, machine learning e dashboards para monitoramento em tempo real e previsão de eventos de inundação.

### 1.1 Objetivo
Fornecer um sistema de alerta precoce capaz de prever inundações urbanas com até 24 horas de antecedência, permitindo ações preventivas e redução de danos.

### 1.2 Escopo
O sistema monitora:
- Níveis de água em pontos críticos
- Precipitação em tempo real
- Umidade do solo
- Padrões históricos de eventos extremos

---

## 2. Arquitetura do Sistema

### 2.1 Visão Geral
```
[Sensores ESP32] → [Coleta de Dados] → [Processamento ML] → [Dashboard] → [Alertas]
```

### 2.2 Componentes Principais

1. **Camada de Sensores**: ESP32 com sensores físicos
2. **Camada de Dados**: Processamento e armazenamento
3. **Camada de Inteligência**: Modelo de Machine Learning
4. **Camada de Apresentação**: Dashboard e alertas

---

## 3. Componentes Hardware

### 3.1 ESP32 DevKit v1
- Microcontrolador principal
- Conectividade WiFi integrada
- Múltiplas entradas analógicas/digitais

### 3.2 Sensores

#### 3.2.1 Sensor de Nível de Água (HC-SR04)
- **Função**: Medir altura da coluna d'água
- **Faixa**: 2cm a 400cm
- **Precisão**: ±3mm
- **Alimentação**: 5V

#### 3.2.2 Sensor de Chuva (YL-83)
- **Função**: Detectar e medir precipitação
- **Tipo**: Resistivo
- **Alimentação**: 3.3V - 5V

#### 3.2.3 Sensor de Umidade do Solo
- **Função**: Medir saturação do solo
- **Faixa**: 0-100% umidade relativa
- **Alimentação**: 3.3V

### 3.3 Diagrama de Conexões

```
ESP32          Sensor
-----          ------
GPIO 34   →    Sensor Nível d'Água
GPIO 35   →    Sensor de Chuva
GPIO 32   →    Sensor Umidade Solo
VCC       →    5V (HC-SR04) / 3.3V (outros)
GND       →    GND
```

---

## 4. Componentes Software

### 4.1 Firmware ESP32 (`esp32_water_level.ino`)
- Leitura de sensores
- Transmissão via WiFi
- Protocolo HTTP/JSON

### 4.2 Modelo de ML (`flood_prediction_model.py`)
- Arquitetura LSTM
- Entrada: sequências de 7 dias
- Saída: probabilidade de inundação

### 4.3 Dashboard (`flood_dashboard.py`)
- Interface Streamlit
- Mapas interativos
- Visualizações em tempo real

### 4.4 Integração de Dados (`data_integration.py`)
- Processamento de dados
- Cálculo de riscos
- Sistema de alertas

---

## 5. Instalação e Configuração

### 5.1 Ambiente de Desenvolvimento

1. **Python 3.8+**
```bash
python --version
```

2. **Arduino IDE 1.8.19+**
- Download: https://www.arduino.cc/en/software

3. **Dependências Python**
```bash
pip install -r requirements.txt
```

### 5.2 Configuração do ESP32

1. **Instalar ESP32 Board Manager**
   - File → Preferences
   - Additional Board Manager URLs: 
     `https://dl.espressif.com/dl/package_esp32_index.json`

2. **Configurar WiFi**
   ```cpp
   const char* ssid = "SUA_REDE_WIFI";
   const char* password = "SUA_SENHA";
   ```

3. **Upload do Código**
   - Tools → Board → ESP32 Dev Module
   - Tools → Port → (selecionar porta COM)
   - Upload

### 5.3 Configuração do Software

1. **Treinar Modelo ML**
```bash
cd src
python flood_prediction_model.py
```

2. **Iniciar Sistema de Dados**
```bash
python data_integration.py
```

3. **Executar Dashboard**
```bash
streamlit run flood_dashboard.py
```

---

## 6. Operação do Sistema

### 6.1 Fluxo de Dados

1. **Coleta**: ESP32 lê sensores a cada 30 segundos
2. **Transmissão**: Dados enviados via HTTP POST
3. **Processamento**: Sistema processa e armazena dados
4. **Análise**: Modelo ML calcula risco de inundação
5. **Alerta**: Sistema emite alertas conforme nível de risco

### 6.2 Níveis de Alerta

- **Verde (0-30%)**: Risco baixo - Monitoramento normal
- **Amarelo (30-70%)**: Risco médio - Atenção redobrada
- **Vermelho (70-100%)**: Risco alto - Ações emergenciais

### 6.3 Dashboard

Acesse: `http://localhost:8501`

**Funcionalidades**:
- Mapa de risco em tempo real
- Gráficos históricos
- Medidor de risco
- Recomendações automáticas

---

## 7. Manutenção

### 7.1 Manutenção Preventiva

**Diária**:
- Verificar status dos sensores
- Monitorar conectividade WiFi

**Semanal**:
- Limpeza dos sensores
- Verificar calibração

**Mensal**:
- Backup dos dados
- Atualização do modelo ML

### 7.2 Calibração de Sensores

**Sensor de Nível d'Água**:
```cpp
float convertToWaterLevel(int rawValue) {
    // Calibrar com medições reais
    return (float)rawValue / 40.96; // Ajustar conforme calibração
}
```

**Sensor de Chuva**:
- Calibrar com pluviômetro de referência
- Ajustar fator de conversão

---

## 8. Troubleshooting

### 8.1 Problemas Comuns

**ESP32 não conecta ao WiFi**:
- Verificar credenciais
- Verificar alcance do sinal
- Resetar ESP32

**Leituras inconsistentes**:
- Verificar conexões dos sensores
- Calibrar sensores
- Verificar alimentação

**Dashboard não carrega**:
- Verificar se Streamlit está rodando
- Verificar porta 8501
- Verificar dependências Python

**Modelo ML com baixa precisão**:
- Verificar qualidade dos dados de treino
- Aumentar período de coleta
- Retreinar modelo

### 8.2 Logs do Sistema

**Localização**:
- ESP32: Serial Monitor (115200 baud)
- Python: Console/terminal
- Streamlit: Browser console

**Exemplo de log normal**:
```
[INFO] WiFi conectado: 192.168.1.100
[INFO] Sensores inicializados
[INFO] Dados enviados: {water_level: 45.2, rainfall: 2.1, moisture: 67.8}
[INFO] Risco calculado: 0.23 (Baixo)
```

---

**Versão do documento**: 1.0
**Última atualização**: 04/06/2025
