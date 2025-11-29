import asyncio
import json
import logging
import os
import tempfile

import azure.functions as func
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from msgraph import GraphServiceClient

from models import Cards, Transactions, Users

ingest_sp_bp = func.Blueprint()


@ingest_sp_bp.function_name(name="IngestSharePointFilesTimer")
@ingest_sp_bp.schedule(
    schedule="0 */2 * * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False
)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info("The timer is past due!")

    files_metadata = asyncio.run(retrieve_sharepoint_files())
    logging.info(files_metadata)

    sharepoint_files = asyncio.run(download_sharepoint_files(files_metadata))

    logging.info("Python timer trigger function executed.")


async def retrieve_sharepoint_files():
    """Download files from SharePoint Site"""

    graph_client = generate_graph_client()

    try:

        credential = DefaultAzureCredential()

        vault_url = os.getenv("vault_url")
        secret_client = SecretClient(vault_url=vault_url, credential=credential)

        drive_id = secret_client.get_secret("sharepoint-site-drive-id").value

        files_to_download = []

        items = (
            await graph_client.drives.by_drive_id(drive_id)
            .items.by_drive_item_id("root:/General:")
            .children.get()
        )

        if items and items.value:
            for item in items.value:
                file_metadata = {
                    "id": item.id,
                    "name": item.name,
                    "web_url": item.web_url,
                    "last_modified": item.last_modified_date_time,
                }

                files_to_download.append(file_metadata)

        return files_to_download

    except Exception as e:
        logging.error(f"An error occurred downloading file from SharePoint: {e}")


async def download_sharepoint_files(files_metadata):
    """Download SharePoint files"""

    graph_client = generate_graph_client()

    credential = DefaultAzureCredential()

    vault_url = os.getenv("vault_url")
    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    drive_id = secret_client.get_secret("sharepoint-site-drive-id").value

    file_paths = []

    for file_metadata in files_metadata:
        try:
            drive_item_id = file_metadata["id"]
            name = file_metadata["name"]

            temp_file_path = tempfile.gettempdir()
            file_path = os.path.join(temp_file_path, name)

            download = (
                await graph_client.drives.by_drive_id(drive_id)
                .items.by_drive_item_id(drive_item_id)
                .content.get()
            )

            with open(file_path, "wb") as file:
                file.write(download)

            file_data = {"name": name, "path": file_path}

            file_paths.append(file_data)
        except Exception as e:
            logging.error(f"An error occurred downloading {name}: {e}")

    return file_paths


def generate_graph_client():
    """Create instance of Microsoft Graph client"""

    try:

        vault_url = os.getenv("vault_url")

        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=vault_url, credential=credential)

        client_id = secret_client.get_secret("sharepoint-client-id").value
        client_secret = secret_client.get_secret("sharepoint-client-secret").value
        tenant_id = secret_client.get_secret("sharepoint-tenant-id").value

        credential = ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
        )

        scopes = ["https://graph.microsoft.com/.default"]
        graph_client = GraphServiceClient(credentials=credential, scopes=scopes)

        return graph_client
    except Exception as e:
        logging.error(f"An error occurred generating graph client: {e}")
