# =============================================================================
# ANÁLISE ESTATÍSTICA DE DADOS DE INUNDAÇÃO EM R
# Global Solution 2025.1 - FIAP
# Sistema HydroAlert - Grupo 35
# =============================================================================

# Carregando bibliotecas necessárias
if (!require(readr)) install.packages("readr")
if (!require(dplyr)) install.packages("dplyr")
if (!require(ggplot2)) install.packages("ggplot2")
if (!require(corrplot)) install.packages("corrplot")
if (!require(forecast)) install.packages("forecast")
if (!require(lubridate)) install.packages("lubridate")

library(readr)
library(dplyr)
library(ggplot2)
library(corrplot)
library(forecast)
library(lubridate)

# =============================================================================
# 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS
# =============================================================================

cat("🔄 Carregando dados de sensores...\n")

# Função para carregar dados de múltiplos sensores
load_sensor_data <- function() {
    # Lista de arquivos de dados (ajustado para procurar na pasta correta)
    data_files <- c(
        file.path("..", "data", "SP001_sensor_data.csv"),
        file.path("..", "data", "RJ001_sensor_data.csv"),
        file.path("..", "data", "BL001_sensor_data.csv")
    )
    # Se não encontrar, tenta na pasta 'data' na raiz do projeto
    if (!file.exists(data_files[1])) {
        data_files <- c(
            file.path("data", "SP001_sensor_data.csv"),
            file.path("data", "RJ001_sensor_data.csv"),
            file.path("data", "BL001_sensor_data.csv")
        )
    }
    all_data <- data.frame()
    for (file in data_files) {
        if (file.exists(file)) {
            sensor_id <- gsub(".*([A-Z]{2}[0-9]{3})_sensor_data.csv", "\\1", file)
            data <- read_csv(file, show_col_types = FALSE)
            data$sensor_id <- sensor_id
            all_data <- rbind(all_data, data)
            cat("✅ Carregado:", sensor_id, "- Registros:", nrow(data), "\n")
        } else {
            cat("⚠️ Arquivo não encontrado:", file, "\n")
        }
    }
    return(all_data)
}

# Carregar dados
flood_data <- load_sensor_data()

# Converter timestamp para formato de data
flood_data$timestamp <- as.POSIXct(flood_data$timestamp)
flood_data$date <- as.Date(flood_data$timestamp)
flood_data$hour <- hour(flood_data$timestamp)

cat("📊 Total de registros carregados:", nrow(flood_data), "\n")
cat("📅 Período dos dados:", min(flood_data$date), "a", max(flood_data$date), "\n")

# =============================================================================
# 2. ANÁLISE ESTATÍSTICA DESCRITIVA
# =============================================================================

cat("\n📈 ANÁLISE ESTATÍSTICA DESCRITIVA\n")
cat("=================================\n")

# Estatísticas resumidas
stats_summary <- flood_data %>%
    group_by(sensor_id) %>%
    summarise(
        count = n(),
        rainfall_mean = round(mean(rainfall, na.rm = TRUE), 2),
        rainfall_sd = round(sd(rainfall, na.rm = TRUE), 2),
        rainfall_max = round(max(rainfall, na.rm = TRUE), 2),
        water_level_mean = round(mean(water_level, na.rm = TRUE), 2),
        water_level_sd = round(sd(water_level, na.rm = TRUE), 2),
        water_level_max = round(max(water_level, na.rm = TRUE), 2),
        moisture_mean = round(mean(soil_moisture, na.rm = TRUE), 2),
        moisture_sd = round(sd(soil_moisture, na.rm = TRUE), 2),
        .groups = 'drop'
    )

print(stats_summary)

# =============================================================================
# 3. ANÁLISE DE CORRELAÇÃO
# =============================================================================

cat("\n🔗 ANÁLISE DE CORRELAÇÃO\n")
cat("=======================\n")

# Matriz de correlação
correlation_data <- flood_data %>%
    select(rainfall, water_level, soil_moisture) %>%
    na.omit()

cor_matrix <- cor(correlation_data)
print(round(cor_matrix, 3))

# Salvar gráfico de correlação
png("data/correlation_analysis_R.png", width = 800, height = 600)
corrplot(cor_matrix, 
         method = "color",
         type = "upper",
         order = "hclust",
         tl.cex = 1.2,
         tl.col = "black",
         title = "Matriz de Correlação - Dados de Sensores\nHydroAlert System")
dev.off()

cat("📊 Gráfico de correlação salvo em: data/correlation_analysis_R.png\n")

# =============================================================================
# 4. ANÁLISE TEMPORAL E TENDÊNCIAS
# =============================================================================

cat("\n⏰ ANÁLISE TEMPORAL\n")
cat("==================\n")

# Análise por hora do dia
hourly_analysis <- flood_data %>%
    group_by(hour) %>%
    summarise(
        avg_rainfall = mean(rainfall, na.rm = TRUE),
        avg_water_level = mean(water_level, na.rm = TRUE),
        avg_moisture = mean(soil_moisture, na.rm = TRUE),
        .groups = 'drop'
    )

# Gráfico de tendências horárias
png("data/hourly_trends_R.png", width = 1200, height = 800)
par(mfrow = c(2, 2))

# Precipitação por hora
plot(hourly_analysis$hour, hourly_analysis$avg_rainfall,
     type = "b", col = "blue", lwd = 2,
     main = "Precipitação Média por Hora",
     xlab = "Hora do Dia", ylab = "Precipitação (mm)",
     pch = 16)
grid()

# Nível de água por hora
plot(hourly_analysis$hour, hourly_analysis$avg_water_level,
     type = "b", col = "red", lwd = 2,
     main = "Nível de Água Médio por Hora",
     xlab = "Hora do Dia", ylab = "Nível de Água (cm)",
     pch = 16)
grid()

# Umidade do solo por hora
plot(hourly_analysis$hour, hourly_analysis$avg_moisture,
     type = "b", col = "green", lwd = 2,
     main = "Umidade do Solo Média por Hora",
     xlab = "Hora do Dia", ylab = "Umidade (%)",
     pch = 16)
grid()

dev.off()

cat("📊 Gráficos de tendências horárias salvos em: data/hourly_trends_R.png\n")

# =============================================================================
# 5. DETECÇÃO DE EVENTOS EXTREMOS
# =============================================================================

cat("\n⚠️ DETECÇÃO DE EVENTOS EXTREMOS\n")
cat("===============================\n")

# Definir thresholds para eventos extremos
rainfall_threshold <- quantile(flood_data$rainfall, 0.95, na.rm = TRUE)
water_level_threshold <- quantile(flood_data$water_level, 0.95, na.rm = TRUE)

cat("🌧️ Threshold precipitação (95º percentil):", round(rainfall_threshold, 2), "mm\n")
cat("🌊 Threshold nível de água (95º percentil):", round(water_level_threshold, 2), "cm\n")

# Identificar eventos extremos
extreme_events <- flood_data %>%
    mutate(
        extreme_rainfall = rainfall > rainfall_threshold,
        extreme_water_level = water_level > water_level_threshold,
        extreme_event = extreme_rainfall | extreme_water_level
    ) %>%
    filter(extreme_event == TRUE)

cat("🚨 Eventos extremos detectados:", nrow(extreme_events), "\n")

# Análise por sensor
extreme_by_sensor <- extreme_events %>%
    group_by(sensor_id) %>%
    summarise(
        count = n(),
        max_rainfall = max(rainfall, na.rm = TRUE),
        max_water_level = max(water_level, na.rm = TRUE),
        .groups = 'drop'
    )

print(extreme_by_sensor)

# =============================================================================
# 6. MODELAGEM PREDITIVA SIMPLES
# =============================================================================

cat("\n🤖 MODELAGEM PREDITIVA SIMPLES\n")
cat("==============================\n")

# Modelo de regressão linear para prever nível de água baseado na precipitação
model_data <- flood_data %>%
    select(rainfall, water_level, soil_moisture) %>%
    na.omit()

# Modelo linear
linear_model <- lm(water_level ~ rainfall + soil_moisture, data = model_data)

cat("📊 Resumo do Modelo Linear:\n")
summary(linear_model)

# Calcular R²
r_squared <- summary(linear_model)$r.squared
cat("📈 R² do modelo:", round(r_squared, 4), "\n")

# =============================================================================
# 7. RELATÓRIO FINAL
# =============================================================================

cat("\n📋 RELATÓRIO FINAL DA ANÁLISE EM R\n")
cat("==================================\n")

# Criar relatório resumido
report <- list(
    total_records = nrow(flood_data),
    sensors_analyzed = length(unique(flood_data$sensor_id)),
    date_range = paste(min(flood_data$date), "a", max(flood_data$date)),
    extreme_events = nrow(extreme_events),
    correlation_rainfall_water = round(cor(flood_data$rainfall, flood_data$water_level, use = "complete.obs"), 3),
    correlation_rainfall_moisture = round(cor(flood_data$rainfall, flood_data$soil_moisture, use = "complete.obs"), 3),
    model_r_squared = round(r_squared, 4),
    avg_rainfall = round(mean(flood_data$rainfall, na.rm = TRUE), 2),
    avg_water_level = round(mean(flood_data$water_level, na.rm = TRUE), 2),
    avg_moisture = round(mean(flood_data$soil_moisture, na.rm = TRUE), 2)
)

# Salvar relatório como JSON para integração com Python
library(jsonlite)
write_json(report, "data/r_analysis_report.json", pretty = TRUE)

cat("✅ Análise completa!\n")
cat("📊 Registros analisados:", report$total_records, "\n")
cat("🔗 Correlação chuva-água:", report$correlation_rainfall_water, "\n")
cat("📈 R² do modelo preditivo:", report$model_r_squared, "\n")
cat("🚨 Eventos extremos:", report$extreme_events, "\n")
cat("💾 Relatório salvo em: data/r_analysis_report.json\n")

cat("\n🎯 ANÁLISE EM R CONCLUÍDA COM SUCESSO!\n")
