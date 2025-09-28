from flask import Flask, render_template, jsonify
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)

# Fetch connection string from environment variables
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "idslog"  # The container storing the log files

if not CONNECTION_STRING:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not set.")

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

@app.route('/')
def index():
    try:
        logs = []
        # List blobs (log files) in the container
        for blob in container_client.list_blobs():
            logs.append(blob.name)

        if not logs:
            return render_template('index.html', logs=None)

        # Fetch the content of each log file
        log_contents = {}
        for log in logs:
            blob_client = container_client.get_blob_client(log)
            download_stream = blob_client.download_blob()
            content = download_stream.readall().decode('utf-8')  # Decode bytes to string
            log_contents[log] = content

        return render_template('index.html', logs=log_contents)

    except Exception as e:
        return render_template('index.html', logs=None, error=str(e))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
