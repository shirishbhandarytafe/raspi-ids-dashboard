from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import StringIO
import os

app = Flask(__name__)

# ================= CONFIG =================
BLOB_ACCOUNT = "idslogsstore123"   # your storage account name
CONTAINER = "idslogs"              # your container name
# Store SAS token in App Settings under SAS_TOKEN
SAS_TOKEN = os.environ.get("SAS_TOKEN")

if not SAS_TOKEN:
    print("⚠️ Warning: SAS_TOKEN is not set. Please add it in App Settings.")
# ==========================================


def fetch_logs():
    """Fetch last 10 CSV logs from blob storage."""
    if not SAS_TOKEN:
        return []

    blob_url = f"https://{BLOB_ACCOUNT}.blob.core.windows.net"
    service = BlobServiceClient(account_url=blob_url, credential=SAS_TOKEN)
    container_client = service.get_container_client(CONTAINER)

    blobs = sorted(container_client.list_blobs(), key=lambda b: b.last_modified, reverse=True)
    last_files = blobs[:10]

    dataframes = []
    for blob in last_files:
        downloader = container_client.download_blob(blob.name)
        content = downloader.readall().decode("utf-8")
        try:
            df = pd.read_csv(StringIO(content))
            df["Filename"] = blob.name
            dataframes.append(df)
        except Exception:
            continue

    return pd.concat(dataframes, ignore_index=True) if dataframes else []


@app.route("/")
def index():
    logs_df = fetch_logs()
    if isinstance(logs_df, list):  # no data
        return render_template("index.html", tables=[], message="No logs found")
    return render_template("index.html", tables=[logs_df.to_dict(orient="records")], message=None)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
