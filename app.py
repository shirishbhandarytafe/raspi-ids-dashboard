from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)

# ================= CONFIG =================
CONTAINER = "idslog"
CONNECTION_STRING = os.environ.get("CONNECTION_STRING")  # set in App Service
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

@app.route("/check-sas")
def check_sas():
    try:
        container_client = blob_service_client.get_container_client(CONTAINER)
        blob_names = [b.name for b in container_client.list_blobs()]
        return "<br>".join(blob_names) if blob_names else "No blobs visible"
    except Exception as e:
        return f"Error accessing container: {e}"

@app.route("/")
def index():
    logs = []
    try:
        container_client = blob_service_client.get_container_client(CONTAINER)
        blobs = list(container_client.list_blobs())
        blobs.sort(key=lambda x: x.name, reverse=True)
        for b in blobs[:10]:
            blob_data = container_client.download_blob(b.name).readall()
            try:
                df = pd.read_csv(BytesIO(blob_data))
                logs.append({"filename": b.name, "rows": df.to_dict(orient="records")})
            except Exception as e:
                logs.append({"filename": b.name, "rows": [], "error": str(e)})
    except Exception as e:
        logs.append({"error": str(e)})
    return render_template("index.html", logs=logs)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
