from flask import Flask, render_template
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# ================= CONFIG =================
STORAGE_ACCOUNT_URL = "https://idslogsstore123.blob.core.windows.net/idslogs"
CONTAINER = "idslogs"

# Use Managed Identity for authentication
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url=STORAGE_ACCOUNT_URL, credential=credential)
container_client = blob_service_client.get_container_client(CONTAINER)
# =========================================

def read_last_logs(n=10):
    """Fetch the last n CSV logs from Azure Blob Storage"""
    try:
        blobs = list(container_client.list_blobs())
    except Exception as e:
        print(f"Error accessing container: {e}")
        return []

    if not blobs:
        return []

    # Sort by last modified descending
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
    """Test route to confirm Managed Identity is working"""
    try:
        # Test listing blobs
        _ = list(container_client.list_blobs())
        return "Managed Identity access working!"
    except Exception as e:
        return f"Access failed: {e}"

if __name__ == "__main__":
    app.run(debug=True)
