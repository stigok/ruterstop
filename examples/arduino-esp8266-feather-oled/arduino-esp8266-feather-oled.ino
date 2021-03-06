/*
Connect to WiFi and query a URL for a payload to be printed on an LCD screen.
This code is somewhat specific for an Adafruit HUZZAH with an OLED FeatherWing
attached.

Author: stigok (stig@stigok.com)
*/

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266HTTPClient.h>

#define OLED_RESET 3
Adafruit_SSD1306 display(OLED_RESET);

#ifndef STASSID
#define STASSID "your-ssid"
#define STAPSK  "your-password"
#endif

const char* ssid = STASSID;
const char* password = STAPSK;
const char* url = "http://192.168.0.7:4000/6013"; // Stig

WiFiClient client;
HTTPClient http;

void setup() {
  // Serial init
  Serial.begin(115200);

  // Display init
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C); // Address 0x3C for 128x32
  display.setTextSize(1);
  display.setTextColor(WHITE);
  clear();

  log("WiFi connecting:\n");
  log(String(ssid) + '\n');

  WiFi.mode(WIFI_STA); // client mode (not AP)
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    log(".");
    delay(500);
  }

  clear();
  log("Connected!\n");
  log("IP:" + WiFi.localIP().toString() + '\n');
  delay(3000);

  // keep-alive
  http.setReuse(true);
}

void clear() {
  display.clearDisplay();
  display.setCursor(0, 0);
  Serial.println("--- display cleared ---");
}

void log(String s) {
  display.print(s);
  display.display();
  Serial.print(s);
}

void error(String s) {
  clear();
  log(String("err: ") + s + '\n');
  delay(3000);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    error("lost wifi connection.\nrestarting...");
    ESP.restart();
    return;
  }

  if (!http.begin(client, url)) {
    error("http unable to connect\n");
    return;
  }

  int code = http.GET();
  if (code <= 0) {
    error(String("HTTP error (") + http.errorToString(code).c_str() + ")\n");
    return;
  }

  String payload = http.getString();
  clear();
  log(payload);

  http.end();

  Serial.println("done. sleeping...");
  delay(5000);
}
