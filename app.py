from flask import Flask, render_template
from azure.storage.blob import ContainerClient
import pandas as pd
from io import StringIO
import os

app = Flask(__name__)

# ========== CONFIG ==========
ACCOUNT_NAME = "idslogsstore123"   # your storage account name
CONTAINER = "idslogs"

# SAS token (set this as environment variable in Azure App Settings)
SAS_TOKEN = os.environ.get("AZURE_STORAGE_SAS_TOKEN")

if not SAS_TOKEN:
    print("⚠️ Warning: SAS token not found. Set AZURE_STORAGE_SAS_TOKEN in App Settings.")
# ============================


@app.route("/")
def index():
    logs = []

    try:
        if not SAS_TOKEN:
            return render_template("index.html", logs=logs)

        # Build container client using SAS
        container_url = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER}?{SAS_TOKEN}"
        container_client = ContainerClient.from_container_url(container_url)

        # Get last 10 blobs (sorted by name/time)
        blob_list = sorted(
            container_client.list_blobs(),
            key=lambda b: b.name,
            reverse=True
        )[:10]

        # Parse each CSV blob into log records
        for blob in blob_list:
            blob_data = container_client.download_blob(blob.name).content_as_text()
            df = pd.read_csv(StringIO(blob_data))
            logs.extend(df.to_dict(orient="records"))

    except Exception as e:
        print(f"❌ Error: {e}")

    return render_template("index.html", logs=logs)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
