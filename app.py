from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)

# ================= CONFIG =================
CONN_STR = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER = "idslogs"

if CONN_STR:
    try:
        blob_service_client = BlobServiceClient.from_connection_string(CONN_STR)
        container_client = blob_service_client.get_container_client(CONTAINER)
        blob_available = True
    except Exception as e:
        print(f"Error initializing BlobServiceClient: {e}")
        blob_available = False
else:
    print("AZURE_STORAGE_CONNECTION_STRING not set")
    blob_available = False
# =========================================

def read_last_logs(n=10):
    """Fetch the last n CSV logs from Azure Blob Storage"""
    if not blob_available:
        return []

    blobs = list(container_client.list_blobs())
    if not blobs:
        return []

    # Sort blobs by last modified date descending
    blobs.sort(key=lambda b: b.last_modified, reverse=True)
    last_blobs = blobs[:n]

    all_logs = []
    for b in last_blobs:
        try:
            data = container_client.download_blob(b.name).readall()
            df = pd.read_csv(BytesIO(data))
            df['LogFile'] = b.name  # Add filename column
            all_logs.append(df)
        except Exception as e:
            print(f"Error reading {b.name}: {e}")

    if all_logs:
        return pd.concat(all_logs, ignore_index=True).to_dict(orient="records")
    return []

@app.route("/")
def index():
    logs = read_last_logs(10)
    return render_template("index.html", logs=logs)

@app.route("/env")
def test_env():
    """Test route to confirm connection string availability"""
    return CONN_STR or "Connection string not set"

if __name__ == "__main__":
    app.run(debug=True)
