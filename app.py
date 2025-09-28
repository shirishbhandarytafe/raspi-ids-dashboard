from flask import Flask, render_template
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# ================= CONFIG =================
STORAGE_ACCOUNT = "idslogsstoregroup1"
CONTAINER_NAME = "idslog"

# Managed Identity credential
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=credential
)

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
        logs.append({"error": f"Error accessing container: {e}"})

    return render_template("index.html", logs=logs)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
