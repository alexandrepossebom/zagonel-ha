# Zagonel Smart Shower - Home Assistant Integration

[![HACS Compatible](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io)

Custom integration for Home Assistant that connects to Zagonel smart showers (Ducali Smart Banho) via cloud API, exposing shower usage sensors.

---

**[Portugues](#portugues)** | **[English](#english)**

---

## Portugues

### Sobre

Integra chuveiros inteligentes Zagonel (app Ducali Smart Banho) ao Home Assistant via API cloud. Expoe sensores de leitura com dados de cada banho: temperatura, consumo de agua, energia, custo e mais.

### Requisitos

- Home Assistant 2024.1+
- [HACS](https://hacs.xyz) instalado
- Conta no app Ducali Smart Banho com chuveiro(s) cadastrado(s)

### Instalacao via HACS

1. Abra o HACS no Home Assistant
2. Clique em **Integracoes** > menu **...** (tres pontos) > **Repositorios personalizados**
3. Adicione o repositorio:
   - URL: `https://github.com/alexandrepossebom/zagonel-ha`
   - Categoria: **Integracao**
4. Clique em **Adicionar**
5. Busque "Zagonel Smart Shower" e clique em **Baixar**
6. Reinicie o Home Assistant

### Instalacao manual

1. Copie a pasta `custom_components/zagonel` para o diretorio `config/custom_components/` do seu Home Assistant
2. Reinicie o Home Assistant

### Configuracao

1. Va em **Configuracoes** > **Dispositivos e Servicos** > **Adicionar Integracao**
2. Busque "Zagonel"
3. Insira o e-mail e senha da sua conta no app Ducali Smart Banho
4. Pronto! Seus chuveiros aparecerao como dispositivos com sensores

### Sensores disponiveis

Cada chuveiro registrado cria os seguintes sensores:

#### Ultimo banho

| Sensor | Unidade | Descricao |
|--------|---------|-----------|
| Last Shower | data/hora | Inicio do ultimo banho |
| Last Shower Duration | segundos | Duracao do ultimo banho |
| Last Shower Temperature | °C | Temperatura media |
| Last Shower Flow Rate | L/min | Vazao media |
| Last Shower Water | L | Agua consumida |
| Last Shower Energy | kWh | Energia consumida |
| Last Shower Power | W | Potencia media |
| Last Shower Voltage | V | Tensao da rede |
| Last Shower Cost | BRL | Custo estimado |

#### Acumulado mensal

| Sensor | Unidade | Descricao |
|--------|---------|-----------|
| Showers This Month | - | Numero de banhos no mes |
| Monthly Water Usage | L | Agua total do mes |
| Monthly Energy Usage | kWh | Energia total do mes |
| Monthly Cost | BRL | Custo total do mes |

O sensor "Showers This Month" inclui a lista completa de banhos do mes como atributo, acessivel via templates:

```yaml
{{ state_attr('sensor.NOME_DO_CHUVEIRO_showers_this_month', 'showers') }}
```

### Energy Dashboard

Os sensores de energia e agua sao compativeis com o Energy Dashboard do Home Assistant:

1. Va em **Configuracoes** > **Dashboards** > **Energia**
2. Em **Dispositivos individuais**, adicione o sensor de energia mensal
3. Em **Agua**, adicione o sensor de agua mensal

### Intervalo de atualizacao

Os dados sao atualizados a cada **10 minutos** via polling na API cloud da Zagonel.

---

## English

### About

Integrates Zagonel smart showers (Ducali Smart Banho app) with Home Assistant via cloud API. Exposes read-only sensors with data from each shower: temperature, water usage, energy, cost and more.

### Requirements

- Home Assistant 2024.1+
- [HACS](https://hacs.xyz) installed
- Ducali Smart Banho app account with registered shower(s)

### Installation via HACS

1. Open HACS in Home Assistant
2. Click **Integrations** > **...** menu (three dots) > **Custom repositories**
3. Add the repository:
   - URL: `https://github.com/alexandrepossebom/zagonel-ha`
   - Category: **Integration**
4. Click **Add**
5. Search for "Zagonel Smart Shower" and click **Download**
6. Restart Home Assistant

### Manual installation

1. Copy the `custom_components/zagonel` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

### Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "Zagonel"
3. Enter the email and password from your Ducali Smart Banho app account
4. Done! Your showers will appear as devices with sensors

### Available sensors

Each registered shower creates the following sensors:

#### Last shower

| Sensor | Unit | Description |
|--------|------|-------------|
| Last Shower | datetime | Start time of the last shower |
| Last Shower Duration | seconds | Duration of the last shower |
| Last Shower Temperature | °C | Average temperature |
| Last Shower Flow Rate | L/min | Average flow rate |
| Last Shower Water | L | Water consumed |
| Last Shower Energy | kWh | Energy consumed |
| Last Shower Power | W | Average power |
| Last Shower Voltage | V | Grid voltage |
| Last Shower Cost | BRL | Estimated cost |

#### Monthly totals

| Sensor | Unit | Description |
|--------|------|-------------|
| Showers This Month | - | Number of showers this month |
| Monthly Water Usage | L | Total water this month |
| Monthly Energy Usage | kWh | Total energy this month |
| Monthly Cost | BRL | Total cost this month |

The "Showers This Month" sensor includes the full list of showers for the month as an attribute, accessible via templates:

```yaml
{{ state_attr('sensor.SHOWER_NAME_showers_this_month', 'showers') }}
```

### Energy Dashboard

The energy and water sensors are compatible with Home Assistant's Energy Dashboard:

1. Go to **Settings** > **Dashboards** > **Energy**
2. Under **Individual devices**, add the monthly energy sensor
3. Under **Water**, add the monthly water sensor

### Update interval

Data is updated every **10 minutes** by polling the Zagonel cloud API.

---

## License

MIT
