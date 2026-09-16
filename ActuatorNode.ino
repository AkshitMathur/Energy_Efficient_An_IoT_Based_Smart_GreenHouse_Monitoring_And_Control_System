actuator node:
#include <SPI.h>
#include <LoRa.h>

// ---------- LoRa Pins ----------
#define SS    5
#define RST   14
#define DIO0  2

// ---------- Relay Pins ----------
#define FAN_PIN    22
#define LIGHT_PIN  21
#define PUMP_PIN   15

// ============================================================
void setup()
{
  Serial.begin(115200);

  // Setup relays (default OFF)
  pinMode(FAN_PIN, OUTPUT);
  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);

  digitalWrite(FAN_PIN, HIGH);
  digitalWrite(LIGHT_PIN, HIGH);
  digitalWrite(PUMP_PIN, HIGH);

  // LoRa setup
  LoRa.setPins(SS, RST, DIO0);

  if (!LoRa.begin(433E6))
  {
    Serial.println("LoRa init failed!");
    while (1);
  }

  // Match Raspberry Pi settings
  LoRa.setSpreadingFactor(7);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(5);
  LoRa.enableCrc();

  Serial.println("Actuator Node Ready — Fan | Light | Pump");
}

// ============================================================
// Remove garbage characters
// ============================================================
String cleanMessage(String msg)
{
  String clean = "";

  for (int i = 0; i < msg.length(); i++)
  {
    char c = msg[i];
    if (c >= 32 && c <= 126)
      clean += c;
  }

  return clean;
}

// ============================================================
void loop()
{
  int packetSize = LoRa.parsePacket();

  if (packetSize)
  {
    String raw = "";

    while (LoRa.available())
      raw += (char)LoRa.read();

    raw.trim();

    Serial.print("RAW: ");
    Serial.println(raw);

    // 🔥 Clean noise
    String message = cleanMessage(raw);

    Serial.print("CLEAN: ");
    Serial.println(message);

    // 🔍 Find command start
    int startIndex = message.indexOf("....");

    if (startIndex == -1)
    {
      Serial.println("→ Not a command (ignored)");
      return;
    }

    message = message.substring(startIndex);

    Serial.print("CMD: ");
    Serial.println(message);

    // ========================================================
    // FAN CONTROL
    // ========================================================
    if (message.startsWith("....FAN:ON"))
    {
      digitalWrite(FAN_PIN, LOW);
      Serial.println("→ Fan ON");
      sendAck("ACK:FAN:ON");
    }
    else if (message.startsWith("....FAN:OFF"))
    {
      digitalWrite(FAN_PIN, HIGH);
      Serial.println("→ Fan OFF");
      sendAck("ACK:FAN:OFF");
    }

    // ========================================================
    // LIGHT CONTROL
    // ========================================================
    else if (message.startsWith("....LIGHT:ON"))
    {
      digitalWrite(LIGHT_PIN, LOW);
      Serial.println("→ Light ON");
      sendAck("ACK:LIGHT:ON");
    }
    else if (message.startsWith("....LIGHT:OFF"))
    {
      digitalWrite(LIGHT_PIN, HIGH);
      Serial.println("→ Light OFF");
      sendAck("ACK:LIGHT:OFF");
    }

    // ========================================================
    // PUMP CONTROL
    // ========================================================
    else if (message.startsWith("....PUMP:ON"))
    {
      digitalWrite(PUMP_PIN, LOW);
      Serial.println("→ Pump ON");
      sendAck("ACK:PUMP:ON");
    }
    else if (message.startsWith("....PUMP:OFF"))
    {
      digitalWrite(PUMP_PIN, HIGH);
      Serial.println("→ Pump OFF");
      sendAck("ACK:PUMP:OFF");
    }

    else
    {
      Serial.println("→ Unknown command");
    }

    Serial.print("RSSI: ");
    Serial.println(LoRa.packetRssi());
  }
}

// ============================================================
// Send ACK
// ============================================================
void sendAck(String msg)
{
  delay(100);

  LoRa.beginPacket();
  LoRa.print(msg);
  LoRa.endPacket();

  Serial.print("ACK sent: ");
  Serial.println(msg);
}
