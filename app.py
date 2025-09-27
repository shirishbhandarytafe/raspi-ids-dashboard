from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)

# ================= CONFIG =================
CONN_STR = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
if not CONN_STR:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not set")

CONTAINER = "idslogs"

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(CONN_STR)
container_client = blob_service_client.get_container_client(CONTAINER)
# =========================================

def read_last_log():
    """Fetch the most recent CSV log from Azure Blob Storage"""
    blobs = list(container_client.list_blobs())
    if not blobs:
        return pd.DataFrame()  # Empty DataFrame if no files

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

if __name__ == "__main__":
    app.run(debug=True)
