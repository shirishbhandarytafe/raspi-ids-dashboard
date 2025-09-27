from flask import Flask, render_template
from azure.storage.blob import ContainerClient
import pandas as pd
from io import StringIO
import os

app = Flask(__name__)

# ================= CONFIG =================
ACCOUNT_NAME = "idslogsstoregroup1"  # updated storage account
CONTAINER = "idslogs"                # container name
SAS_TOKEN = os.environ.get("SAS_TOKEN")  # must be set in Azure App Settings
# ==========================================

if not SAS_TOKEN:
    print("⚠️ Warning: SAS_TOKEN is not set. Add it in App Settings.")
else:
    print(f"Using SAS token: {SAS_TOKEN[:20]}...")  # just first 20 chars

def fetch_logs():
    logs = []
    if not SAS_TOKEN:
        print("❌ SAS token missing, cannot fetch logs.")
        return logs

    try:
        container_url = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER}?{SAS_TOKEN}"
        container_client = ContainerClient.from_container_url(container_url)

        blob_list = sorted(
            container_client.list_blobs(),
            key=lambda b: b.last_modified,
            reverse=True
        )
        print(f"Found {len(blob_list)} blobs in container '{CONTAINER}'.")

        last_files = blob_list[:10]  # last 10 files
        for blob in last_files:
            print(f"Downloading blob: {blob.name}")
            blob_data = container_client.download_blob(blob.name).content_as_text()
            try:
                df = pd.read_csv(StringIO(blob_data))
                logs.extend(df.to_dict(orient="records"))
            except Exception as e:
                print(f"❌ Failed to parse CSV {blob.name}: {e}")

    except Exception as e:
        print(f"❌ Error fetching logs: {e}")

    return logs

@app.route("/")
def index():
    logs = fetch_logs()
    return render_template("index.html", logs=logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
