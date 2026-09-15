import time
import board
import busio
import digitalio
import adafruit_rfm9x

# SPI setup
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

cs = digitalio.DigitalInOut(board.D17)
reset = digitalio.DigitalInOut(board.D25)

rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)

# Match ESP32 settings
rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5
rfm9x.enable_crc = True

print("LoRa Sender Ready")

while True:
    print("Sending FAN:ON")
    rfm9x.send(bytes("FAN:ON", "utf-8"))
    time.sleep(5)

    print("Sending FAN:OFF")
    rfm9x.send(bytes("FAN:OFF", "utf-8"))
    time.sleep(5)
