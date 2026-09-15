import time
import board
import busio
import digitalio
import adafruit_rfm9x
import json
import datetime
import requests

# =========================
# SUPABASE SETTINGS
# =========================
SUPABASE_URL = "https://kpbaknudinxnvlgamwql.supabase.co"  # CHANGE THIS
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtwYmFrbnVkaW54bnZsZ2Ftd3FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MDEzMjEsImV4cCI6MjA4OTQ3NzMyMX0.9EdgWi09QnTcrA9RP_z90wUx08ArS-tm-q3myf-ffQY"

print("?? Initializing Greenhouse Monitor...")

# =========================
# LORA SETTINGS
# =========================
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D17)
reset = digitalio.DigitalInOut(board.D25)

rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)
rfm9x.spreading_factor = 7

print("? LoRa Receiver Ready")

# =========================
# LOG FILE
# =========================
log_file = "lora_data_log.txt"

# =========================
# SUPABASE FUNCTION
# =========================
def send_to_supabase(data):
    """Send sensor data to Supabase"""
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
            print(f"? Sent to Supabase: {data}")
            return True
        else:
            print(f"? Supabase error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"? Supabase exception: {e}")
        return False

# =========================
# MAIN LOOP
# =========================
print("?? Starting main loop...")
print("Waiting for LoRa packets...\n")

while True:
    packet = rfm9x.receive(timeout=5)

    if packet is not None:
        try:
            # Decode packet
            message = packet.decode("utf-8").strip()
            print(f"?? Raw Received: {message}")

            # Parse sensor data
            # Expected format: "Temp:22.3,Humidity:62.3,Soil:56.8,Light:77.7,CO2:424.8"
            parts = message.split(",")
            data_dict = {}
            
            for part in parts:
                if ":" in part:
                    key, value = part.split(":")
                    data_dict[key.strip()] = float(value.strip())

            # Extract all sensor values
            # Map to your expected keys
            temperature = data_dict.get("Temp", None) or data_dict.get("Temperature", 0)
            humidity = data_dict.get("Hum", 0)
            soil_moisture = data_dict.get("Soil", None) or data_dict.get("SoilMoisture", 0)
            light_intensity = data_dict.get("Light", None) or data_dict.get("LightIntensity", 0)
            co2_level = data_dict.get("CO2", None) or data_dict.get("CO2Level", 0)

            # Log to file
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"{timestamp}, Temp:{temperature}, Hum:{humidity}, Soil:{soil_moisture}, Light:{light_intensity}, CO2:{co2_level}\n"
            
            with open(log_file, "a") as f:
                f.write(log_line)

            # Prepare payload for Supabase
            payload = {
                "temperature": temperature,
                "humidity": humidity,
                "soil_moisture": soil_moisture,
                "light_intensity": light_intensity,
                "co2_level": co2_level
            }
            
            # Send to Supabase
            send_to_supabase(payload)

            print(f"?? RSSI: {rfm9x.last_rssi}")
            print("-" * 60)

        except Exception as e:
            print(f"? Parsing Error: {e}")
            print(f"   Raw message: {message}")

    time.sleep(0.1)
