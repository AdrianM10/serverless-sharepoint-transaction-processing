import asyncio
import json
import logging
import os
import tempfile

import azure.functions as func
import pandas as pd
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from msgraph import GraphServiceClient
from sqlalchemy import text
from sqlmodel import Session

from models import Cards, Transactions, Users, engine, select

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

    ingest_sharepoint_files(sharepoint_files)

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


def ingest_sharepoint_files(sharepoint_files: list[dict]):
    """Ingest records from each sheet in xlsx file"""

    for sharepoint_file in sharepoint_files:

        logging.info(sharepoint_file)

        file_path = sharepoint_file["path"]

        users = pd.read_excel(open(file_path, "rb"), sheet_name="users")

        process_users(sharepoint_file, users)

        cards = pd.read_excel(open(file_path, "rb"), sheet_name="cards")

        process_cards(sharepoint_file, cards)


def process_users(sharepoint_file: dict, users: dict):
    """Process rows from users sheet in xlsx file"""

    for index, row in users.iterrows():

        try:

            row_data = {
                "id": row["id"],
                "current_age": row["current_age"],
                "retirement_age": row["retirement_age"],
                "birth_year": row["birth_year"],
                "birth_month": row["birth_month"],
                "gender": row["gender"],
                "address": row["address"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "per_capita_income": row["per_capita_income"],
                "yearly_income": row["yearly_income"],
                "total_debt": row["total_debt"],
                "credit_score": row["credit_score"],
                "num_credit_cards": row["num_credit_cards"],
            }

            model = Users

            upsert_record(row_data, sharepoint_file, model)
        except Exception as e:
            logging.error(
                f"An error occurred processing {row["id"]} record from users sheet: {e}"
            )
            continue


def process_cards(sharepoint_file, cards):
    """Process rows from cards sheet in xlsx file"""

    for index, row in cards.iterrows():

        try:

            row_data = {
                "id": row["id"],
                "client_id": row["client_id"],
                "card_brand": row["card_brand"],
                "card_type": row["card_type"],
                "card_number": row["card_number"],
                "expires": row["expires"],
                "cvv": row["cvv"],
                "has_chip": row["has_chip"],
                "num_cards_issued": row["num_cards_issued"],
                "credit_limit": row["credit_limit"],
                "acct_open_date": row["acct_open_date"],
                "year_pin_last_changed": row["year_pin_last_changed"],
                "card_on_dark_web": row["card_on_dark_web"],
            }

            model = Cards
            upsert_record(row_data, sharepoint_file, model)

        except Exception as e:
            logging.error(f"An error occurred processing cards: {e}")
            continue


def upsert_record(row_data: dict, sharepoint_file: dict, model):

    try:

        with Session(engine) as session:

            name = sharepoint_file["name"]
            path = sharepoint_file["path"]

            # Check if record exists in table
            statement = select(model).where(model.id == row_data["id"])
            result = session.exec(statement).first()

            if result is None:
                result = model(**row_data)

            # Sync data and update values
            for key, value in row_data.items():
                setattr(result, key, value)

            session.add(result)
            session.commit()

            session.refresh(result)
            logging.info(f"Processed users data")

    except Exception as e:
        logging.error(f"An error occurred inserting record: {e}")
