# Diagrama de Circuito - Sistema de Monitoramento de Inundações

## Esquema de Conexões ESP32

```
                    ESP32 DevKit v1
                   ┌─────────────────┐
                   │                 │
                   │       3V3 ●─────┼─── VCC Sensor Umidade
                   │       GND ●─────┼─── GND (comum)
                   │                 │
     Sensor HC-SR04│      GPIO34 ●───┼─── Trigger/Echo
     (Nível d'Água)│                 │
                   │      GPIO35 ●───┼─── Analog Out (Sensor Chuva)
                   │                 │
                   │      GPIO32 ●───┼─── Analog Out (Sensor Umidade)
                   │                 │
                   │         5V ●────┼─── VCC HC-SR04
                   │                 │
                   └─────────────────┘
```

## Lista de Materiais

| Componente | Quantidade | Descrição |
|------------|------------|-----------|
| ESP32 DevKit v1 | 1 | Microcontrolador principal |
| HC-SR04 | 1 | Sensor ultrassônico de distância |
| YL-83 | 1 | Sensor de chuva |
| Sensor de Umidade | 1 | Sensor capacitivo de umidade do solo |
| Jumpers | 10 | Fios de conexão |
| Protoboard | 1 | Placa de ensaio |
| Resistores 10kΩ | 2 | Pull-up/Pull-down |

## Pinout Detalhado

### ESP32 DevKit v1
```
         ┌─ USB ─┐
         │       │
    3V3  ●       ● VIN
    GND  ●       ● GND
    GPIO15●      ● GPIO13
    GPIO2 ●       ● GPIO12
    GPIO0 ●       ● GPIO14
    GPIO4 ●       ● GPIO27
    GPIO16●       ● GPIO26
    GPIO17●       ● GPIO25
    GPIO5 ●       ● GPIO33
    GPIO18●       ● GPIO32  ← Sensor Umidade
    GPIO19●       ● GPIO35  ← Sensor Chuva
    GPIO21●       ● GPIO34  ← Sensor Nível
    RXD0  ●       ● VN
    TXD0  ●       ● VP
    GPIO22●       ● EN
    GPIO23●       ● 3V3
         └───────┘
```

## Instalação Física

### 1. Sensor de Nível d'Água (HC-SR04)
- **Posicionamento**: 50cm acima do nível máximo esperado
- **Proteção**: Caixa estanque IP65
- **Montagem**: Suporte fixo em poste ou estrutura

### 2. Sensor de Chuva (YL-83)
- **Posicionamento**: Área aberta, sem obstruções
- **Inclinação**: 15° para escoamento
- **Altura**: 1.5m do solo

### 3. Sensor de Umidade do Solo
- **Profundidade**: 15-20cm no solo
- **Distância**: 2m de estruturas de concreto
- **Proteção**: Cabo impermeável

### 4. ESP32
- **Local**: Caixa hermética
- **Alimentação**: Fonte 5V/2A ou bateria + painel solar
- **Antena**: Posição vertical para melhor sinal WiFi

## Configurações de Software

### Calibração dos Sensores

```cpp
// Sensor de Nível (HC-SR04)
float getWaterLevel() {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    
    long duration = pulseIn(echoPin, HIGH);
    float distance = duration * 0.034 / 2;
    
    // Converter distância para nível de água
    float waterLevel = REFERENCE_HEIGHT - distance;
    return max(0, waterLevel);
}

// Sensor de Chuva
float getRainfall() {
    int rawValue = analogRead(RAIN_PIN);
    // Calibrar com pluviômetro de referência
    float rainfall = map(rawValue, 0, 4095, 0, 100);
    return rainfall;
}

// Sensor de Umidade
float getSoilMoisture() {
    int rawValue = analogRead(MOISTURE_PIN);
    // Calibração: 0 = seco, 4095 = úmido
    float moisture = map(rawValue, 0, 4095, 0, 100);
    return moisture;
}
```

## Troubleshooting de Hardware

### Problemas Comuns

1. **Leituras instáveis do HC-SR04**
   - Verificar alimentação 5V estável
   - Adicionar capacitor 100µF na alimentação
   - Verificar cabos não estão muito longos (max 30cm)

2. **Sensor de chuva não responde**
   - Limpar superfície do sensor
   - Verificar se está nivelado
   - Testar com gotas d'água

3. **Umidade do solo sempre 0% ou 100%**
   - Verificar se sensor está bem inserido no solo
   - Calibrar com solo seco e úmido
   - Verificar corrosão nos contatos

### Códigos de Erro

| Código | Descrição | Solução |
|--------|-----------|---------|
| E001 | WiFi não conecta | Verificar SSID/senha |
| E002 | Sensor HC-SR04 timeout | Verificar conexões |
| E003 | Leitura analógica fora do range | Verificar alimentação |
| E004 | Falha no envio HTTP | Verificar conectividade |

## Manutenção Preventiva

### Checklist Semanal
- [ ] Limpeza dos sensores
- [ ] Verificação das conexões
- [ ] Teste de conectividade WiFi
- [ ] Verificação da alimentação

### Checklist Mensal
- [ ] Calibração dos sensores
- [ ] Backup dos dados
- [ ] Verificação da caixa hermética
- [ ] Teste do sistema de alertas

## Expansão do Sistema

### Sensores Adicionais
- Sensor de temperatura/umidade (DHT22)
- Sensor de pressão atmosférica (BMP280)
- Sensor de qualidade do ar (MQ-135)
- Câmera para monitoramento visual

### Comunicação Alternativa
- LoRa para longas distâncias
- GSM/4G para áreas sem WiFi
- Mesh network para múltiplos pontos

---

**Documento**: Diagrama de Circuito v1.0  
**Data**: 04/06/2025  
**Equipe**: Grupo 35 - HydroAlert Solutions
