from azure.storage.blob import BlobServiceClient

# Connect to the public container without credential
account_url = "https://minedbuildings.blob.core.windows.net"
blob_service_client = BlobServiceClient(account_url=account_url, credential=None)

# Access the container
container_client = blob_service_client.get_container_client("northamerica")

# Test listing some blobs
blobs = list(container_client.list_blobs(name_starts_with="mexico"))
for blob in blobs:
    print(blob.name)