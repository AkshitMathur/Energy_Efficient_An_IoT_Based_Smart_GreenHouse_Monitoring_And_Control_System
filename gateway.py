# ============================================================
#  GATEWAY (Raspberry Pi) — LoRa Bridge to Supabase
#  Fixes applied:
#    1. Commands tracked by Supabase row ID (not command string)
#       — ensures re-sends are not silently skipped
#    2. Command sent 3× for reliability, with ACK listening
#    3. Display also shows fan state for easy debugging
#    4. LoRa settings explicitly set (SF7, BW125, CR5, CRC ON)
# ============================================================

import time
import board
import busio
import digitalio
import adafruit_rfm9x
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests

# ============================================================
#  SUPABASE CONFIG
# ============================================================
SUPABASE_URL = "https://kpbaknudinxnvlgamwql.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtwYmFrbnVkaW54bnZsZ2Ftd3FsIiwicm9sZSI6ImFub24iL"
    "CJpYXQiOjE3NzM5MDEzMjEsImV4cCI6MjA4OTQ3NzMyMX0"
    ".9EdgWi09QnTcrA9RP_z90wUx08ArS-tm-q3myf-ffQY"
)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ============================================================
#  OLED DISPLAY  (128×64, I2C 0x3C)
# ============================================================
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
oled.show()

image = Image.new("1", (128, 64))
draw  = ImageDraw.Draw(image)
font  = ImageFont.load_default()


def update_display(temp, hum, soil, light, co2, timestamp, fan_state="?", rssi=None):
    draw.rectangle((0, 0, 128, 64), outline=0, fill=0)

    lines = [
        f"{timestamp[-8:]}  Fan:{fan_state}",
        f"T:{temp:.1f}  H:{hum:.1f}",
        f"S:{soil:.0f}  L:{light:.0f}",
        f"CO2:{co2:.0f}",
    ]

    if rssi is not None:
        lines.append(f"RSSI:{rssi}")

    y = 0
    for line in lines:
        draw.text((0, y), line, font=font, fill=255)
        y += 12

    oled.image(image)
    oled.show()


# ============================================================
#  LORA RADIO
# ============================================================
spi   = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs    = digitalio.DigitalInOut(board.D17)
reset = digitalio.DigitalInOut(board.D25)

rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)

# ---- MUST match actuator node settings exactly ----
rfm9x.spreading_factor  = 7
rfm9x.signal_bandwidth  = 125000
rfm9x.coding_rate       = 5
rfm9x.enable_crc        = True
# ---------------------------------------------------

print("LoRa Gateway Ready")

# ============================================================
#  RUNTIME STATE
# ============================================================
temperature    = 0.0
humidity       = 0.0
soil           = 0.0
light          = 0.0
co2            = 0.0
last_timestamp = "No Data"
current_fan    = "?"

# FIX: track by row ID so the same command value can be
#       re-sent when a new DB row is inserted.
last_command_id   = None
last_command_time = 0


# ============================================================
#  SUPABASE: SEND SENSOR DATA
# ============================================================
def send_to_supabase(data: dict):
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_data",
            json=data,
            headers=HEADERS,
            timeout=5,
        )
    except Exception as e:
        print("Supabase send error:", e)


# ============================================================
#  SUPABASE: FETCH LATEST COMMAND
#  Returns (row_id, "....FAN:ON" | "....FAN:OFF") or (None, None)
# ============================================================
def get_command():
    try:
        # Fetch id + fan from the most recent commands row
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/commands"
            "?select=id,fan&order=created_at.desc&limit=1",
            headers=HEADERS,
            timeout=5,
        )

        if resp.status_code == 200:
            rows = resp.json()
            if rows:
                row = rows[0]
                fan_val = row.get("fan", "").upper()
                row_id  = row.get("id")

                if fan_val == "ON":
                    return row_id, "....FAN:ON"
                elif fan_val == "OFF":
                    return row_id, "....FAN:OFF"

    except Exception as e:
        print("Command fetch error:", e)

    return None, None


# ============================================================
#  LORA: PARSE SENSOR MESSAGE
#  Expected format: "Temp:25.3,Hum:60.1,Soil:512,Light:800,CO2:450"
# ============================================================
def parse_message(message: str) -> dict:
    data_dict = {}
    for part in message.split(","):
        if ":" in part:
            key, _, value = part.partition(":")
            try:
                data_dict[key.strip()] = float(value.strip())
            except ValueError:
                pass
    return data_dict


# ============================================================
#  LORA: SEND COMMAND WITH RETRIES + OPTIONAL ACK WAIT
# ============================================================
def send_command(command: str, retries: int = 3):
    print(f"TX command: {command}")
    for i in range(retries):
        rfm9x.send(bytes(command, "utf-8"))
        time.sleep(0.2)

        # Listen briefly for ACK from actuator
        ack = rfm9x.receive(timeout=0.5)
        if ack:
            try:
                ack_str = ack.decode("utf-8").strip()
                if "ACK" in ack_str:
                    print(f"  ACK received: {ack_str} (attempt {i+1})")
                    return True
            except Exception:
                pass

    print(f"  No ACK after {retries} attempts (command may still have landed).")
    return False


# ============================================================
#  MAIN LOOP
# ============================================================
print("System Started...\n")

last_rssi = None

while True:

    # ----------------------------------------------------------
    # 1. RECEIVE SENSOR DATA
    # ----------------------------------------------------------
    packet = rfm9x.receive(timeout=0.2)

    if packet:
        try:
            msg = packet.decode("utf-8").strip()

            # Skip ACK packets that arrive here unexpectedly
            if "ACK" in msg:
                pass
            else:
                print("RX sensor:", msg)

                data = parse_message(msg)

                temperature = data.get("Temp",  temperature)
                humidity    = data.get("Hum",   humidity)
                soil        = data.get("Soil",  soil)
                light       = data.get("Light", light)
                co2         = data.get("CO2",   co2)

                last_timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                last_rssi      = rfm9x.last_rssi

                payload = {
                    "temperature":    temperature,
                    "humidity":       humidity,
                    "soil_moisture":  soil,
                    "light_intensity": light,
                    "co2_level":      co2,
                }
                send_to_supabase(payload)

        except Exception as e:
            print("Parse error:", e)

    # ----------------------------------------------------------
    # 2. FETCH AND SEND COMMAND
    #    FIX: compare by row ID, not command string value.
    #         This means a new "FAN:ON" row will always trigger
    #         a fresh transmission even if last command was also ON.
    # ----------------------------------------------------------
    if time.time() - last_command_time > 2:
        row_id, command = get_command()

        if row_id and row_id != last_command_id:
            sent = send_command(command)
            last_command_id = row_id

            # Update display fan state
            current_fan = "ON" if "ON" in command else "OFF"

        last_command_time = time.time()

    # ----------------------------------------------------------
    # 3. UPDATE DISPLAY
    # ----------------------------------------------------------
    update_display(
        temperature,
        humidity,
        soil,
        light,
        co2,
        last_timestamp,
        fan_state=current_fan,
        rssi=last_rssi,
    )

    time.sleep(0.1)
