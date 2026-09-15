import time
import board
import busio
import digitalio
import adafruit_rfm9x
import requests

# =========================
# SUPABASE SETTINGS
# =========================
SUPABASE_URL = "https://kpbaknudinxnvlgamwql.supabase.co"  # CHANGE THIS
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtwYmFrbnVkaW54bnZsZ2Ftd3FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MDEzMjEsImV4cCI6MjA4OTQ3NzMyMX0.9EdgWi09QnTcrA9RP_z90wUx08ArS-tm-q3myf-ffQY"


DEVICE_ID = "greenhouse_1"

# =========================
# LORA SETUP
# =========================
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D17)
reset = digitalio.DigitalInOut(board.D25)

rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)

rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5
rfm9x.enable_crc = True

print("?? PI READY")

# =========================
# FETCH COMMAND
# =========================
def fetch_command():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    url = f"{SUPABASE_URL}/rest/v1/commands?status=eq.pending&limit=1"

    response = requests.get(url, headers=headers)

    print("RAW RESPONSE:", response.text)

    if response.status_code == 200:
        data = response.json()
        if len(data) > 0:
            return data[0]

    return None

# =========================
# MARK DONE
# =========================
def mark_done(cmd_id):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{SUPABASE_URL}/rest/v1/commands?id=eq.{cmd_id}"

    try:
        requests.patch(url, json={"status": "done"}, headers=headers)
    except Exception as e:
        print("ERROR UPDATE:", e)

# =========================
# MAIN LOOP
# =========================
while True:

    print("\nChecking Supabase...")

    cmd = fetch_command()

    if cmd:
        command_text = cmd["command"]

        print("? COMMAND FOUND:", command_text)

        # Send via LoRa
        rfm9x.send(bytes(command_text, "utf-8"))
        print("?? SENT TO ESP32")

        # Mark done
        mark_done(cmd["id"])

    else:
        print("? No command")

    time.sleep(5)
