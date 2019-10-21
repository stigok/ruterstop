/*
 *  Based on esp8266/Arduino HTTP over TLS (HTTPS) example sketch
 *  Created by Ivan Grokhotkov, 2015.
 *  https://raw.githubusercontent.com/esp8266/Arduino/d5bb4a99f64a843e28b119d174b90c910516458f/libraries/ESP8266WiFi/examples/HTTPSRequest/HTTPSRequest.ino
 */

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <ESP8266WiFi.h>
#include <WiFiClient.h>
//#include <WiFiClientSecure.h>
#include <ESP8266HTTPClient.h>

#define OLED_RESET 3
Adafruit_SSD1306 display(OLED_RESET);

#define USER_AGENT_STR "foodshop/0.1 (esp8266 / huzzah)"

const char* ssid = "Mr. M";
const char* password = "Lollipop";
const char* url = "http://192.168.1.19:4000/";

// SHA1 fingerprint of a certificate to pin
//const char* fingerprint = "FB B4 E4 23 96 AB 9E 4D 2C 09 97 11 CC 21 BE 58 53 73 84 07";

void setup() {
  // Serial init
  Serial.begin(115200);

  // Display init
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.display();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.setTextColor(WHITE);

  logln("WiFi connecting:");
  logln(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    log(".");
    delay(500);
  }

  clear();
  logln("Connected!");
  logln(WiFi.localIP().toString());
  delay(3000);
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

void logln(String s) {
  log(s);
  display.println();
  Serial.println();
}

void errorln(String s) {
  clear();
  logln(String("err: ") + s);
  delay(3000);
}

void loop() {
  WiFiClient client;
  HTTPClient http;

  if (!http.begin(client, url)) {
    errorln("http unable to connect");
    return;
  }

  int code = http.GET();
  if (code <= 0) {
    errorln(http.errorToString(code).c_str());
    return;
  }

  String payload = http.getString();
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print(payload);
  display.display();

  Serial.println("done. sleeping...");
  delay(3000);
}
