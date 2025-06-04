#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configurações de WiFi
const char* ssid = "SEU_WIFI";
const char* password = "SUA_SENHA";

// Pinos dos sensores
const int waterLevelPin = 34;     // Sensor de nível de água
const int rainfallPin = 35;       // Pluviômetro
const int moisturePin = 32;       // Sensor de umidade do solo

// Servidor para envio de dados
const char* serverName = "https://seu-servidor.com/api/data";

// Intervalo de leitura (ms)
unsigned long lastTime = 0;
unsigned long timerDelay = 30000;  // 30 segundos

void setup() {
  Serial.begin(115200);
  
  WiFi.begin(ssid, password);
  Serial.println("Conectando ao WiFi");
  
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.print("Conectado ao WiFi com IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Verifica se é hora de enviar dados
  if ((millis() - lastTime) > timerDelay) {
    if(WiFi.status() == WL_CONNECTED) {
      // Leitura dos sensores
      int waterLevel = analogRead(waterLevelPin);
      int rainfall = analogRead(rainfallPin);
      int moisture = analogRead(moisturePin);
      
      // Converte leituras em valores significativos
      float waterLevelCm = convertToWaterLevel(waterLevel);
      float rainfallMm = convertToRainfall(rainfall);
      float moisturePercent = convertToMoisture(moisture);
      
      // Exibe valores no Serial Monitor
      Serial.println("Leituras dos sensores:");
      Serial.print("Nível de água: "); Serial.print(waterLevelCm); Serial.println(" cm");
      Serial.print("Precipitação: "); Serial.print(rainfallMm); Serial.println(" mm");
      Serial.print("Umidade do solo: "); Serial.print(moisturePercent); Serial.println(" %");
      
      // Prepara dados para envio
      DynamicJsonDocument doc(1024);
      doc["device_id"] = "ESP32_FLOOD_001";
      doc["water_level"] = waterLevelCm;
      doc["rainfall"] = rainfallMm;
      doc["soil_moisture"] = moisturePercent;
      doc["timestamp"] = millis();
      
      // Converte para string JSON
      String jsonString;
      serializeJson(doc, jsonString);
      
      // Envia dados para servidor
      HTTPClient http;
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");
      
      int httpResponseCode = http.POST(jsonString);
      
      if (httpResponseCode > 0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
      } else {
        Serial.print("Erro no HTTP POST: ");
        Serial.println(httpResponseCode);
      }
      
      http.end();
    } else {
      Serial.println("WiFi Desconectado");
    }
    lastTime = millis();
  }
}

// Funções de conversão de leituras analógicas
float convertToWaterLevel(int rawValue) {
  // Conversão da leitura analógica para centímetros
  // Calibração deve ser feita com o sensor real
  return (float)rawValue / 40.96; // Exemplo: 0-4095 para 0-100cm
}

float convertToRainfall(int rawValue) {
  // Conversão da leitura do pluviômetro para mm
  return (float)rawValue / 40.96; // Exemplo simplificado
}

float convertToMoisture(int rawValue) {
  // Conversão para percentual de umidade
  // 4095 (seco) - 0 (úmido)
  return 100 - ((float)rawValue / 4095.0 * 100);
}