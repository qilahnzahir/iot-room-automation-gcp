import os
from google.cloud import firestore
from google.oauth2 import service_account
import google.auth

PROJECT_ID = "gcp-project-id"
DATABASE_ID = "firestrore-database-id"

if os.path.exists("firestore-key.json"):
    # Local development
    credentials = service_account.Credentials.from_service_account_file(
        "firestore-key.json"
    )
else:
    # Cloud Run (ADC)
    credentials, _ = google.auth.default()

db = firestore.Client(
    project=PROJECT_ID,
    credentials=credentials,
    database=DATABASE_ID
)

def get_telemetry():
    docs = db.collection("room_telemetry") \
             .order_by("timestamp") \
             .stream()
    return [d.to_dict() for d in docs]

def get_events():
    docs = db.collection("room_events") \
             .order_by("timestamp") \
             .stream()
    return [d.to_dict() for d in docs]
