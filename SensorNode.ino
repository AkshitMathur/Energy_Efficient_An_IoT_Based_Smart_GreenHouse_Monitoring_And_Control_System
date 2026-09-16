sensor node:
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <BH1750.h>
#include <SparkFun_SCD4x_Arduino_Library.h>
#include "esp_sleep.h"

#define SS 5
#define RST 14
#define DIO0 2
#define SOIL_PIN 34
#define RELAY_PIN 25

BH1750 lightMeter;
SCD4x scd40;

void setup()
{
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);

  // 🔌 Turn ON sensors
  digitalWrite(RELAY_PIN, LOW);
  Serial.println("Sensors ON");
  delay(3000);

  // I2C
  Wire.begin(21, 22);

  // -------- BH1750 INIT --------
  bool bhReady = false;
  if (lightMeter.begin())
  {
    Serial.println("BH1750 OK");
    bhReady = true;
  }
  else
  {
    Serial.println("BH1750 FAIL");
  }

  // -------- SCD40 INIT --------
  if (scd40.begin())
  {
    Serial.println("SCD40 OK");
    scd40.startPeriodicMeasurement();
  }
  else
    Serial.println("SCD40 FAIL");

  // -------- LoRa INIT --------
  LoRa.setPins(SS, RST, DIO0);
  if (!LoRa.begin(433E6))
  {
    Serial.println("LoRa FAIL");
  }
  Serial.println("LoRa OK");

  // ⏳ wait for SCD40 data
  delay(6000);

  // 🌱 Soil
  long soilValue = 0;
  for (int i = 0; i < 200; i++)
  {
    soilValue += analogRead(SOIL_PIN);
    delay(2);
  }
  soilValue /= 200;

  float soilPercent = map(soilValue, 4095, 250, 0, 100);

  // 💡 Light
  float lux = 0;
  if (bhReady)
  {
    for (int i = 0; i < 5; i++)
    {
      lux += lightMeter.readLightLevel();
      delay(200);
    }
    lux /= 5;
  }
  else
  {
    lux = -1;
  }

  // 🌬️ SCD40
  float temp = 0, hum = 0;
  uint16_t co2 = 0;

  if (scd40.getDataReadyStatus() && scd40.readMeasurement())
  {
    co2 = scd40.getCO2();
    temp = scd40.getTemperature();
    hum = scd40.getHumidity();
  }
  else
  {
    Serial.println("SCD40 not ready");
  }

  // 📟 Serial
  Serial.print("Soil: ");
  Serial.print(soilPercent);
  Serial.print(" | Light: ");
  Serial.print(lux);
  Serial.print(" lx | Temp: ");
  Serial.print(temp);
  Serial.print(" C | Hum: ");
  Serial.print(hum);
  Serial.print(" % | CO2: ");
  Serial.println(co2);

  // 📡 LoRa
  LoRa.beginPacket();
  LoRa.print("....");
  LoRa.print("Soil:");
  LoRa.print(soilPercent);
  LoRa.print(",Light:");
  LoRa.print(lux);
  LoRa.print(",Temp:");
  LoRa.print(temp);
  LoRa.print(",Hum:");
  LoRa.print(hum);
  LoRa.print(",CO2:");
  LoRa.print(co2);
  LoRa.endPacket();

  Serial.println("Sent via LoRa");

  // 🔌 Turn OFF sensors
  digitalWrite(RELAY_PIN, HIGH);
  Serial.println("Sensors OFF");

  // 😴 Sleep
  Serial.println("Sleeping 20 sec...\n");
  esp_sleep_enable_timer_wakeup(20 * 1000000);
  esp_deep_sleep_start();
}

void loop()
{
}
