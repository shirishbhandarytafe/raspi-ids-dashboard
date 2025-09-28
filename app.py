from flask import Flask, jsonify, render_template
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)

# Read connection string from environment variable
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "<YourContainerName>"  # Replace with your container name

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Route to fetch logs from Azure Blob Storage
@app.route('/logs')
def get_logs():
    logs = []
    try:
        # List blobs in the container
        for blob in container_client.list_blobs():
            blob_client = container_client.get_blob_client(blob.name)
            download_stream = blob_client.download_blob()
            content = download_stream.readall().decode('utf-8')  # Decode to string
            logs.append({'name': blob.name, 'content': content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(logs)

# Route to serve the HTML file (Dashboard)
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
