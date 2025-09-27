from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
import os
from io import StringIO

app = Flask(__name__)

# ============== CONFIG ===================
ACCOUNT_URL = "https://idslogsstore123.blob.core.windows.net"
CONTAINER_NAME = "idslogs"
SAS_TOKEN = os.environ.get("AZURE_STORAGE_SAS_URL")
# =========================================

# Safe check
if not SAS_TOKEN:
    print("⚠️ Warning: SAS token not set. The app will run, but no logs can be loaded.")
    blob_service_client = None
    container_client = None
else:
    blob_service_client = BlobServiceClient(account_url=ACCOUNT_URL, credential=SAS_TOKEN)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)


@app.route("/")
def index():
    log_files = []
    logs_data = []

    if container_client:
        # List all blobs and sort by last modified
        blobs = list(container_client.list_blobs())
        blobs = sorted(blobs, key=lambda b: b.last_modified, reverse=True)

        # Get up to last 10 CSV logs
        for blob in blobs[:10]:
            if blob.name.endswith(".csv"):
                log_files.append(blob.name)

                # Download blob content
                blob_data = container_client.download_blob(blob.name).readall()
                try:
                    df = pd.read_csv(StringIO(blob_data.decode("utf-8")))
                    logs_data.append({
                        "name": blob.name,
                        "table": df.to_html(classes="table table-striped table-bordered", index=False)
                    })
                except Exception as e:
                    logs_data.append({
                        "name": blob.name,
                        "table": f"<p>Error reading CSV: {e}</p>"
                    })

    return render_template("index.html", log_files=log_files, logs_data=logs_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
