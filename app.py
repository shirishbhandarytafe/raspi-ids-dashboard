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

def read_last_log():
    """Fetch the most recent CSV log from Azure Blob Storage"""
    if not blob_available:
        return pd.DataFrame()  # Empty DataFrame if blob storage not accessible

    blobs = list(container_client.list_blobs())
    if not blobs:
        return pd.DataFrame()  # No files found

    # Sort blobs by last modified date descending
    blobs.sort(key=lambda b: b.last_modified, reverse=True)
    last_blob = blobs[0]

    # Download blob content
    blob_data = container_client.download_blob(last_blob.name).readall()
    df = pd.read_csv(BytesIO(blob_data))
    return df

@app.route("/")
def index():
    try:
        df = read_last_log()
        logs = df.to_dict(orient="records")
    except Exception as e:
        logs = []
        print(f"Error reading blob: {e}")
    return render_template("index.html", logs=logs)

@app.route("/env")
def test_env():
    """Test route to confirm connection string availability"""
    return CONN_STR or "Connection string not set"

if __name__ == "__main__":
    app.run(debug=True)
