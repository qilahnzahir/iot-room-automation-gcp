#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// ================== WIFI CONFIG ==================
const char* ssid = "SSID";
const char* password = "PASSWORD";

// ================== MQTT CONFIG ==================
const char* mqttServer = "MQTT.BROKER.EXTERNAL.IP.ADRESS";
const int mqttPort = 8883;
const char* mqttUser = "MQTT_USERNAME";
const char* mqttPass = "MQTT_PASSWORD";

// ================== CA CERT ==================
const char* ca_cert = R"EOF(
-----BEGIN CERTIFICATE-----
Add CA certificate here
-----END CERTIFICATE-----
)EOF";

// ================== PIN DEFINITIONS ==================
const int pirPin    = 14;
const int relayPin  = 32;   // FAN
const int ledPin    = 19;   // LED
const int btnFanPin = 33;   // FAN button
const int btnLedPin = 25;   // LED button

// ================== TIMING ==================
const unsigned long idleBuffer = 30000;        // 30 seconds
const unsigned long overrideDuration = 15000; // 15 seconds

// ================== VARIABLES ==================
volatile bool motionDetected = false;
unsigned long lastMotionTime = 0;

unsigned long fanOverrideStartTime = 0;
unsigned long ledOverrideStartTime = 0;

bool occupied = false;
bool fanON = false;
bool ledON = false;
bool fanManualOverride = false;
bool ledManualOverride = false;

// ================== MQTT ==================
WiFiClientSecure espClient;
PubSubClient client(espClient);

// ================== PIR INTERRUPT ==================
void IRAM_ATTR motionISR() {
  motionDetected = true;
  lastMotionTime = millis();
}

// ================== WIFI ==================
void connectWiFi() {
  Serial.print("Connecting WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

// ================== MQTT ==================
void connectMQTT() {
  Serial.println("Connecting MQTT...");
  while (!client.connected()) {
    if (client.connect("room01", mqttUser, mqttPass)) {
      Serial.println("MQTT connected (TLS)");
    } else {
      Serial.print("MQTT failed rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// ================== MQTT PUBLISH ==================
void publishStatus(const char* event) {
  char payload[200];
  snprintf(payload, sizeof(payload),
    "{\"occupied\":%d,\"fan\":%d,\"led\":%d,\"fan_override\":%d,\"led_override\":%d}",
    occupied, fanON, ledON, fanManualOverride, ledManualOverride
  );

  client.publish("building/room01/status", payload);
  client.publish("building/room01/event", event);
}

// ================== SETUP ==================
void setup() {
  Serial.begin(9600);

  pinMode(pirPin, INPUT);
  pinMode(relayPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(btnFanPin, INPUT_PULLUP);
  pinMode(btnLedPin, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(pirPin), motionISR, RISING);

  connectWiFi();
  espClient.setCACert(ca_cert);
  client.setServer(mqttServer, mqttPort);
  connectMQTT();

  Serial.println("System Ready");
}

// ================== LOOP ==================
void loop() {
  client.loop();
  unsigned long now = millis();

  // -------- FAN BUTTON --------
  if (digitalRead(btnFanPin) == LOW) {
    fanON = !fanON;
    fanManualOverride = true;
    fanOverrideStartTime = now;
    digitalWrite(relayPin, fanON ? HIGH : LOW);
    publishStatus("MANUAL_FAN");
    delay(300);
  }

  // -------- LED BUTTON --------
  if (digitalRead(btnLedPin) == LOW) {
    ledON = !ledON;
    ledManualOverride = true;
    ledOverrideStartTime = now;
    digitalWrite(ledPin, ledON ? HIGH : LOW);
    publishStatus("MANUAL_LED");
    delay(300);
  }

  // -------- OVERRIDE TIMEOUT --------
  if (fanManualOverride && (now - fanOverrideStartTime > overrideDuration)) {
    fanManualOverride = false;
    Serial.println("Fan override expired");
  }

  if (ledManualOverride && (now - ledOverrideStartTime > overrideDuration)) {
    ledManualOverride = false;
    Serial.println("LED override expired");
  }

  // -------- PIR MOTION --------
  if (motionDetected) {
    motionDetected = false;
    occupied = true;

    if (!fanManualOverride) {
      fanON = true;
      digitalWrite(relayPin, HIGH);
    }
    if (!ledManualOverride) {
      ledON = true;
      digitalWrite(ledPin, HIGH);
    }

    publishStatus("AUTO_ON");
  }

  // -------- IDLE TIMEOUT (BLOCKED DURING OVERRIDE) --------
  if (occupied &&
      (now - lastMotionTime > idleBuffer) &&
      !fanManualOverride &&
      !ledManualOverride) {

    occupied = false;
    fanON = false;
    ledON = false;

    digitalWrite(relayPin, LOW);
    digitalWrite(ledPin, LOW);

    publishStatus("AUTO_OFF");
  }
}
