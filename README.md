# 🌱 Smart Greenhouse Environment Monitoring and Control System

An IoT-based greenhouse monitoring and control system that automates the measurement and regulation of key environmental parameters — temperature, humidity, soil moisture, light intensity, and CO₂ — using long-range LoRa communication, a Raspberry Pi gateway, and a real-time cloud dashboard.

<p align="center">
  <img src="https://img.shields.io/badge/Status-Completed-brightgreen" alt="status" />
  <img src="https://img.shields.io/badge/Platform-ESP32%20%7C%20Raspberry%20Pi-blue" alt="platform" />
  <img src="https://img.shields.io/badge/Communication-LoRa%20SX1278-orange" alt="communication" />
  <img src="https://img.shields.io/badge/Cloud-Supabase-3ECF8E" alt="cloud" />
</p>

---

## 📖 Overview

Manual monitoring of greenhouse conditions is labour-intensive, inconsistent, and difficult to scale. This project replaces manual checks with an automated, low-power, long-range IoT pipeline: environmental sensors feed an ESP32 sensor node, data travels over LoRa to a Raspberry Pi gateway, gets stored in the Supabase cloud, and is visualized in real time on a web dashboard — which can also send control commands back to actuators (ventilation fan, irrigation pump, and lighting).

The system was designed and built as part of the **Project Based Learning (0701230605)** course, Department of Electronics and Telecommunication Engineering, **Symbiosis Institute of Technology, Pune**.

> 📌 This repository currently includes the **Raspberry Pi gateway scripts** (LoRa ↔ Supabase bridge, OLED status display) along with the project report, presentation, and dashboard UI. ESP32 firmware and the dashboard frontend are not included.

## ✨ Features

- 📡 **Long-range wireless sensing** via SX1278 LoRa modules (low power, large coverage vs. Wi-Fi)
- 🌡️ **Multi-parameter monitoring**: temperature, humidity, soil moisture, light intensity, and CO₂ concentration
- ☁️ **Cloud integration** with Supabase using REST APIs (HTTP POST for sensor data, HTTP GET for control commands)
- 📊 **Real-time dashboard** (Figma-designed) with live readings, historical trends (24h / 7d / 30d / all-time), min/avg/max stats, and out-of-range alerts
- 🎛️ **Dual control modes** — automatic threshold-based control and manual override from the dashboard
- 🔋 **Energy-efficient sensor node** using ESP32 deep sleep mode to extend battery life
- 🏗️ **Physical prototype** built with an acrylic enclosure housing sensors, actuators, and wiring

## 🏛️ System Architecture

```mermaid
flowchart LR
    subgraph Greenhouse
        A[Temp Sensor - DHT11]
        B[Humidity Sensor - DHT11]
        C[Soil Moisture Sensor]
        D[Light Sensor - BH1750]
        E[CO2 Sensor - SCD40]
    end

    A & B & C & D & E --> F[ESP32 Sensor Node]
    F -- LoRa SX1278 --> G[Raspberry Pi 5 Gateway]
    G -- HTTP REST API --> H[(Supabase Cloud)]
    H --> I[Web Dashboard]
    I --> J[User]
    G -- LoRa SX1278 --> K[ESP32 Actuator Node]
    K --> L[Ventilation Fan / Irrigation Pump / Grow Lights]
    I -. control commands .-> H
    H -. commands .-> G
```

**Data flow:**
1. The ESP32 **sensor node** reads temperature, humidity, soil moisture, light intensity, and CO₂ from the connected sensors.
2. Readings are transmitted wirelessly over **LoRa (SX1278)** to a **Raspberry Pi 5 gateway**.
3. The gateway pushes data to **Supabase** via HTTP POST and polls it via HTTP GET for pending control commands.
4. The **web dashboard** visualizes live and historical data and lets users trigger manual actions.
5. Control commands flow back through the gateway over LoRa to the **ESP32 actuator node**, which drives the ventilation fan, irrigation pump, and lighting via a relay module.

## 🛠️ Tech Stack & Hardware

| Component | Details |
|---|---|
| Microcontroller | ESP32 (sensor node + actuator node) |
| Gateway | Raspberry Pi 5 |
| Wireless Communication | SX1278 LoRa module, 433 MHz, SPI |
| Temperature & Humidity | DHT11 |
| Light Intensity | BH1750 (I²C, 1–65535 lux) |
| Soil Moisture | Analog soil moisture sensor (3.3–5V) |
| CO₂ | SCD40 (I²C, 400–5000 ppm) |
| Actuators | Ventilation fan, irrigation pump, grow lights (via relay module) |
| Cloud / Backend | Supabase (real-time database + REST API) |
| Dashboard | Figma-designed web UI |
| Enclosure | Acrylic sheet model (~20 × 15 × 15 in) |

## 📊 Dashboard Preview

The dashboard includes four main sections:

- **Dashboard** — live parameter cards (temperature, humidity, soil moisture, light intensity, CO₂) with optimal-range bars and High/Low/Normal status badges, plus an overall system status indicator
- **Controls** — toggle switches for ventilation fan, water pump, and grow lights, with quick actions ("Cool Down", "Water Now") and a "Turn Off All" option
- **Analytics & History** — historical trend charts (24 Hours / 7 Days / 30 Days / All Time) with min/avg/max summaries and data export
- **Alerts** — notifications when parameters fall outside optimal ranges

## 📁 Repository Structure

```
smart-greenhouse-monitoring/
├── gateway/
│   ├── lora_sensor_supabase.py     # LoRa receiver → parses sensor packets → pushes to Supabase
│   ├── lora_final.py               # Polls Supabase for pending commands → sends over LoRa to actuator node
│   ├── oled_display_lora_sensor.py # LoRa receiver + live OLED status display + Supabase upload
│   ├── lora_send_test.py           # Standalone LoRa TX test script (sends FAN:ON / FAN:OFF)
│   ├── .env.example                # Template for Supabase credentials (copy to .env, fill in, never commit .env)
│   └── requirements.txt
├── docs/
│   ├── report.pdf                  # Full project report
│   ├── presentation.pptx           # Final review presentation
│   └── datasheets/                 # Component datasheets (BH1750, SCD40, ESP32, SX1278, Raspberry Pi)
├── dashboard-screens/
│   └── dashboard.pdf               # UI screens: login, dashboard, controls, analytics
├── photos/
│   ├── greenhouse-model.jpg
│   ├── gateway-oled.jpg
│   ├── sensor-node-interior.jpg
│   └── actuator-node-interior.jpg
├── .gitignore
└── README.md
```

> ESP32 sensor/actuator firmware and the dashboard frontend are not included yet — add them under `firmware/` and `dashboard/` if you upload that code later.

## 🚀 Running the Gateway Scripts

These scripts run on the **Raspberry Pi gateway** and require an RFM9x LoRa HAT/module wired via SPI (and an SSD1306 OLED over I²C for `oled_display_lora_sensor.py`).

### 1. Install dependencies
```bash
pip install adafruit-circuitpython-rfm9x adafruit-circuitpython-ssd1306 pillow requests python-dotenv
```

### 2. Configure Supabase credentials
Create a `.env` file in `gateway/` (this file is git-ignored, **never commit it**):
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```
Each script then loads these at the top instead of hardcoding them:
```python
import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
```

> ⚠️ **Security note:** earlier versions of these scripts had the Supabase key hardcoded directly in the source. If that key was ever pushed to a public repo or shared, regenerate it from your Supabase project settings before going further.

### 3. Run
```bash
# Receive sensor data over LoRa and upload to Supabase
python gateway/lora_sensor_supabase.py

# Poll Supabase for pending commands and forward to the actuator node over LoRa
python gateway/lora_final.py

# Receive sensor data, show it on the OLED, and upload to Supabase
python gateway/oled_display_lora_sensor.py

# Standalone LoRa send test (no Supabase needed)
python gateway/lora_send_test.py
```

`lora_sensor_supabase.py` and `oled_display_lora_sensor.py` expect incoming LoRa packets in the format:
```
Temp:22.3,Humidity:62.3,Soil:56.8,Light:77.7,CO2:424.8
```

## 📈 Results

- Stable, packet-loss-free point-to-point LoRa communication between the sensor node and gateway, verified via RSSI monitoring
- Reliable real-time data flow from sensors → ESP32 → LoRa → Raspberry Pi → Supabase → dashboard
- Deep sleep mode reduced ESP32 idle current draw from hundreds of mA to a few µA, significantly extending battery life
- Functional automatic and manual control of ventilation, irrigation, and lighting

## 🔮 Future Scope

- Integration of pH and nutrient sensors for deeper soil analysis
- Machine learning-based predictive control using historical data
- Mobile app with push notifications/alerts
- Solar-powered nodes for full energy autonomy
- Scaling to multi-greenhouse / large-area deployments

## 📚 References

Key datasheets and papers referenced during development are listed in [`docs/report.pdf`](docs/report.pdf), including datasheets for the BH1750, SCD40, ESP32, SX1278, and Raspberry Pi 4/5, plus IoT/LoRa smart-agriculture literature.

## 📄 License

This project was developed for academic purposes as part of a Project Based Learning course. Add a license (e.g., MIT) here if you intend to open-source it for wider use.
