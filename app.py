from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)

# ================= CONFIG =================
CONTAINER_NAME = "idslog"  # Your container
CONNECTION_STRING = os.environ.get("CONNECTION_STRING")

if not CONNECTION_STRING:
    raise RuntimeError("⚠️ CONNECTION_STRING environment variable not set.")

# Build BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

@app.route("/")
def index():
    logs = []
    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blobs = list(container_client.list_blobs())
        blobs.sort(key=lambda x: x.name, reverse=True)  # latest first

        for b in blobs[:10]:  # last 10 logs
            blob_data = container_client.download_blob(b.name).readall()
            try:
                df = pd.read_csv(BytesIO(blob_data))
                logs.append({
                    "filename": b.name,
                    "rows": df.to_dict(orient="records"),
                    "size": len(blob_data)
                })
            except Exception as e:
                logs.append({
                    "filename": b.name,
                    "rows": [],
                    "size": len(blob_data),
                    "error": str(e)
                })
    except Exception as e:
        print(f"Error accessing container: {e}")

    return render_template("index.html", logs=logs)

# Optional route to test connection
@app.route("/check-connection")
def check_connection():
    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        count = len(list(container_client.list_blobs()))
        return f"✅ Connection successful! {count} blobs found."
    except Exception as e:
        return f"❌ Connection failed: {e}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

