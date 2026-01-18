# IoT Room Occupancy Monitoring and Energy-Efficient Automation System
CPC357 IOT ARCHITECTURE AND SMART APPLICATIONS (ASSIGNMENT)

## System Description
An IoT-based room occupancy monitoring and energy-efficient automation system using NodeMCU ESP32-S, PIR sensor, relay-controlled fan, and LED with manual override using push buttons, developed using Google Cloud Platform.

---------------------
## Repository Structure

```
iot-room-autmation-gcp/
│
├── README.md                     # Project documentation
│
├── firmware/
│   └── smart_room_control.ino    # ESP32 Firmware that handle the logic and publish topic to MQTT
|
├── pythonSubscriber/ 
│   └── mqtt_to_firestore.py      # Backend that subscribe to MQTT topics and store data to Firestore
│
├── dashboard/                    
│   ├── app.py                    # Main Streamlit App
│   └── analytic.py               # Analytic and Functions for Data Visualization
│   └── firestore_client.py       # Firestore connection and data handling
│   └── requirements.txt          # Dashboard dependencies and required library
│   └── Dockerfile                # Instructions for building dashboard image
│   └── main.py                   # Entrypoint for deployment setup on Cloud Run
│
└── docs/                             # Documentation and resources
    └── dashboard_screenshot/         # System screenshots for documentation
```

---------------------
## Security Features
- MQTT Communication using TLS on port 8883
- MQTT username/password authentication
- IAM service accounts with least privilege
- Authenticated dashboard (Streamlit) access using Firebase Authentication

This project is developed for academic purposes for CPC357 IoT Architecture and Smart Application.
