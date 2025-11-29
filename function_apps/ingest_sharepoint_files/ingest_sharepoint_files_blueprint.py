import asyncio
import logging
import os
import json


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

    sharepoint_files = asyncio.run(download_sharepoint_files())

    logging.info("Python timer trigger function executed.")


async def download_sharepoint_files():
    """Download files from SharePoint Site"""

    try:

        graph_client = generate_graph_client()
        credential = DefaultAzureCredential()

        vault_url = os.getenv("vault_url")
        secret_client = SecretClient(
            vault_url=vault_url, credential=credential)

        drive_id = secret_client.get_secret("sharepoint-site-drive-id").value
        logging.info(drive_id)

        # List files under General channel
        result = await graph_client.drives.by_drive_id(drive_id).list_.items.get()

        logging.info(result)

    except Exception as e:
        logging.error(
            f"An error occurred downloading file from SharePoint: {e}")


def generate_graph_client():
    """Create instance of Microsoft Graph client"""

    try:

        vault_url = os.getenv("vault_url")

        credential = DefaultAzureCredential()
        secret_client = SecretClient(
            vault_url=vault_url, credential=credential)

        client_id = secret_client.get_secret("sharepoint-client-id").value
        client_secret = secret_client.get_secret(
            "sharepoint-client-secret").value
        tenant_id = secret_client.get_secret("sharepoint-tenant-id").value

        credential = ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
        )

        scopes = ["https://graph.microsoft.com/.default"]
        graph_client = GraphServiceClient(
            credentials=credential, scopes=scopes)

        return graph_client
    except Exception as e:
        logging.error(f"An error occurred generating graph client: {e}")
