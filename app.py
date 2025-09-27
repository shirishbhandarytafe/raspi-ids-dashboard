from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)

# ================= CONFIG =================
CONTAINER = "idslogsgroup1"  # Replace with your new container name
SAS_TOKEN = os.environ.get("SAS_TOKEN")
STORAGE_ACCOUNT = "idslogsstoregroup1"  # Replace with your storage account name

if not SAS_TOKEN:
    print("⚠️ SAS_TOKEN environment variable not set. Logs will not be displayed.")

# Build blob service client
blob_service_client = None
if SAS_TOKEN:
    blob_service_client = BlobServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=SAS_TOKEN
    )

@app.route("/")
def index():
    logs = []
    if blob_service_client:
        try:
            container_client = blob_service_client.get_container_client(CONTAINER)
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
