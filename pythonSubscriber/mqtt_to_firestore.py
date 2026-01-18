import ssl
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from google.cloud import firestore
from google.oauth2 import service_account

# ================= FIRESTORE =================
SERVICE_ACCOUNT_FILE = "firestore-key.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE
)

db = firestore.Client(credentials=credentials)

# ================= MQTT =================
MQTT_BROKER = " MQTT_BROKER_IP_ADDRESS"
MQTT_PORT = 8883
MQTT_TOPIC = "building/room1/#"

MQTT_USER = "MQTT_USERNAME"
MQTT_PASS = "MQTT_PASSWORD"

CA_FILE = "/etc/mosquitto/certs/ca.crt"

# ================= CALLBACKS =================
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT, rc =", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        data["timestamp"] = datetime.utcnow().isoformat()

        db.collection("room_telemetry").add(data)
        print("Saved:", data)
    except Exception as e:
        print("Error:", e)

# ================= CLIENT =================
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)

client.tls_set(
    ca_certs=CA_FILE,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

#  Start the MQTT loop 
try: 
    client.loop_forever() 
except KeyboardInterrupt: 
    print("\nScript interrupted by user. Exiting...") 
    client.disconnect() 
