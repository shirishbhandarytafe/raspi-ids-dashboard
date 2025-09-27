from flask import Flask, render_template
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)

# ================= CONFIG =================
# Must set this environment variable on the system:
# export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
CONN_STR = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
if not CONN_STR:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not set")

CONTAINER = "idslogs"
# =========================================

# Initialize Blob Service
blob_service = BlobServiceClient.from_connection_string(CONN_STR)
container_client = blob_service.get_container_client(CONTAINER)

def get_last_logs(n=10):
    """Fetch last n CSV log files from Azure container and merge into one DataFrame"""
    blobs = sorted(container_client.list_blobs(), key=lambda b: b.name, reverse=True)
    df_list = []
    count = 0
    for blob in blobs:
        if blob.name.endswith(".csv"):
            stream = container_client.download_blob(blob.name).readall()
            df = pd.read_csv(BytesIO(stream))
            df_list.append(df)
            count += 1
            if count >= n:
                break
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return pd.DataFrame()

def render_table(df):
    """Convert DataFrame to HTML table with color-coded anomalies"""
    html = '<table id="ids-table" class="display table table-striped table-bordered">'
    # Header
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    # Rows
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            if col.lower() == "ml label":
                cls = "normal" if str(row[col]).lower() == "normal" else "anomaly"
                html += f'<td class="{cls}">{row[col]}</td>'
            else:
                html += f'<td>{row[col]}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

@app.route("/")
def index():
    df = get_last_logs()
    if df.empty:
        return "<h2>No logs found</h2>"
    table_html = render_table(df)
    return render_template("index.html", table=table_html)

if __name__ == "__main__":
    # Run on all network interfaces so it can be accessed from LAN
    app.run(host="0.0.0.0", port=5000, debug=True)
