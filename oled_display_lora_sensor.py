import time
import board
import busio
import digitalio
import adafruit_rfm9x
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests

# ================== SUPABASE SETTINGS ==================
SUPABASE_URL = "https://kpbaknudinxnvlgamwql.supabase.co"
SUPABASE_KEY = "YOUR_KEY_HERE"

print("Initializing Greenhouse Monitor")

# ================== OLED SETUP ==================
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

def update_display(temp, hum, soil, light, co2, timestamp, rssi=None):
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

    lines = [
        f"Last:{timestamp[-8:]}",
        f"Temp:{temp:.1f}C Hum:{hum:.1f}%",
        f"Soil:{soil:.1f}",
        f"Light:{light:.1f}",
        f"CO2:{co2:.1f}"
    ]

    y_positions = [0, 12, 24, 36, 48]

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (oled.width - w) // 2   # 👈 center align
        draw.text((x, y_positions[i]), line, font=font, fill=255)

    oled.image(image)
    oled.show()

# ================== LORA SETUP ==================
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D17)
reset = digitalio.DigitalInOut(board.D25)

rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)
rfm9x.spreading_factor = 7

print("LoRa Receiver Ready")

# ================== LOG FILE ==================
log_file = "lora_data_log.txt"

# ================== SUPABASE FUNCTION ==================
def send_to_supabase(data):
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_data",
            json=data,
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            print("Sent to Supabase")
            return True
        else:
            print(f"Supabase error: {response.status_code}")
            return False

    except Exception as e:
        print(f"Supabase exception: {e}")
        return False

# ================== DEFAULT VALUES ==================
temperature = 0
humidity = 0
soil_moisture = 0
light_intensity = 0
co2_level = 0
last_timestamp = "No Data"

print("Starting main loop...")
print("Waiting for LoRa packets...\n")

# ================== MAIN LOOP ==================
while True:
    packet = rfm9x.receive(timeout=5)

    if packet is not None:
        try:
            message = packet.decode("utf-8").strip()
            print(f"Received: {message}")

            # Parse data
            parts = message.split(",")
            data_dict = {}

            for part in parts:
                if ":" in part:
                    key, value = part.split(":")
                    data_dict[key.strip()] = float(value.strip())

            # Extract values
            temperature = data_dict.get("Temp", data_dict.get("Temperature", 0))
            humidity = data_dict.get("Hum", data_dict.get("Humidity", 0))
            soil_moisture = data_dict.get("Soil", data_dict.get("SoilMoisture", 0))
            light_intensity = data_dict.get("Light", data_dict.get("LightIntensity", 0))
            co2_level = data_dict.get("CO2", data_dict.get("CO2Level", 0))

            # Timestamp
            last_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Log to file
            with open(log_file, "a") as f:
                f.write(f"{last_timestamp}, {message}\n")

            # Send to Supabase
            payload = {
                "temperature": temperature,
                "humidity": humidity,
                "soil_moisture": soil_moisture,
                "light_intensity": light_intensity,
                "co2_level": co2_level
            }

            send_to_supabase(payload)

            print(f"RSSI: {rfm9x.last_rssi}")
            print("-" * 50)

        except Exception as e:
            print(f"Parsing Error: {e}")

    # ✅ ALWAYS update display (even if no packet)
    update_display(
        temperature,
        humidity,
        soil_moisture,
        light_intensity,
        co2_level,
        last_timestamp,
        rfm9x.last_rssi if packet else None
    )

    time.sleep(0.1)
