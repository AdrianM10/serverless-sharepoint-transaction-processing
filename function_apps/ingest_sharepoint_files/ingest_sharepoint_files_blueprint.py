import asyncio
import datetime
import logging
import os
import re
import tempfile
from itertools import batched

import azure.functions as func
import pandas as pd
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from msgraph import GraphServiceClient
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from models import (
    Cards,
    DataImport,
    SQLModel,
    Transactions,
    Users,
    engine,
    insert,
    or_,
    select,
)

ingest_sp_bp = func.Blueprint()


@ingest_sp_bp.function_name(name="IngestSharePointFilesTimer")
@ingest_sp_bp.schedule(
    schedule="0 */30 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def timer_trigger(myTimer: func.TimerRequest, context: func.Context) -> None:
    if myTimer.past_due:
        logging.info("The timer is past due!")

    yearly_directories = retrieve_yearly_directories()

    if yearly_directories:
        for yearly_directory in yearly_directories:
            monthly_directories = retrieve_monthly_directories(yearly_directory)

            logging.info(f"monthly_directories: {monthly_directories}")

            if monthly_directories:
                # Retrieve files from monthly subdirectory
                files_to_process = []

                for month_directory in monthly_directories:
                    path_relative_to_root = (
                        f"root:/General/Transactions/Finance/YE2010/{month_directory}:"
                    )
                    logging.info(path_relative_to_root)

                    retrieved_files = asyncio.run(retrieve_files(path_relative_to_root))

                    files_to_process.extend(retrieved_files)

                logging.info(files_to_process)

                # Call helper function to add file metadata to DataImport table
                import_file_metadata(files_to_process)

                # Call helper function to read data_import table to identify file
                # sources that need to be ingested based on status columns
                files_to_download = process_data_import_table()

                sharepoint_files = asyncio.run(
                    download_sharepoint_files(files_to_download)
                )
                logging.info("Starting import job for sharepoint files...")
                asyncio.run(ingest_sharepoint_files(sharepoint_files, context))
                logging.info("Finished import job")

    logging.info("Python timer trigger function executed.")


def retrieve_yearly_directories() -> list[str] | None:
    """
    Retrieve sharepoint directories (Yearly)

    Returns:
        list[str] | None: A list of yearly directory names matching the pattern 'YE' followed by
                          a 4 digit year (e.g YE2010, YE2011... ) or None if an error is encountered
    """

    try:
        path_relative_to_root = "root:/General/Transactions/Finance:"
        pattern = r"^YE\d{4}$"

        yearly_directories = asyncio.run(
            retrieve_sharepoint_directories(path_relative_to_root, pattern)
        )

        return yearly_directories
    except Exception as e:
        logging.error(f"An error occurred retrieving yearly directories: {e}")
        return None


def retrieve_monthly_directories(yearly_directory: str) -> list[str] | None:
    """
    Retrieve sharepoint directories (Monthly) for a given year

    Args:
        yearly_directory (str): Directory name for a given year

    Returns:
        list[str] | None: A list of monthly directory names matching a 6 digit pattern
                          (e.g 201001, 201002, 201003...) or None if an error is encountered
    """

    try:
        path_relative_to_root = (
            f"root:/General/Transactions/Finance/{yearly_directory}:"
        )

        # Monthly directories
        pattern = r"^\d{6}$"
        retrieved_monthly_directories = asyncio.run(
            retrieve_sharepoint_directories(path_relative_to_root, pattern)
        )

        return retrieved_monthly_directories

    except Exception as e:
        logging.error(f"An error occurred retrieving monthly directories: {e}")
        return None


async def retrieve_sharepoint_directories(
    path_relative_to_root: str, pattern: str
) -> list[str] | None:
    """
    Retrieve directories in SharePoint site matching yearly or monthly pattern i.e 'YE2010

    Args:
        path_relative_to_root (str) : SharePoint path relative to the drive root
        pattern (str) : Regex pattern matching yearly or monthly directory pattern

    Returns:
            list[str] : Subdirectories listed under path relative to root or None if an error is encountered

    """

    try:
        graph_client = generate_graph_client()

        credential = DefaultAzureCredential()

        vault_url = os.getenv("vault_url")
        secret_client = SecretClient(vault_url=vault_url, credential=credential)
        drive_id = secret_client.get_secret("sharepoint-site-drive-id").value

        logging.info(drive_id)

        directories = []

        items = (
            await graph_client.drives.by_drive_id(drive_id)
            .items.by_drive_item_id(path_relative_to_root)
            .children.get()
        )

        if items and items.value:
            for item in items.value:
                if re.match(pattern, item.name):
                    directories.append(item.name)

        return directories

    except Exception as e:
        logging.error(f"An error occurred retrieving sharepoint directories: {e}")
        return None


async def retrieve_files(path_relative_to_root: str) -> list[dict] | None:
    """
    Retrieve file(s) metadata containing file 'id', 'name', 'created_date_time', 'last_modified_date_time'

    Args:
        path_relative_to_root (str): SharePoint path relative to the drive root

    Returns:
            list[dict]: Metadata for files listed under directory or None if an error is encountered

    """

    graph_client = generate_graph_client()

    credential = DefaultAzureCredential()

    vault_url = os.getenv("vault_url")
    secret_client = SecretClient(vault_url=vault_url, credential=credential)
    drive_id = secret_client.get_secret("sharepoint-site-drive-id").value

    files_to_process = []

    try:
        items = (
            await graph_client.drives.by_drive_id(drive_id)
            .items.by_drive_item_id(path_relative_to_root)
            .children.get()
        )

        if items and items.value:
            for item in items.value:
                file_metadata = {
                    "id": item.id,
                    "size": item.size,
                    "file_name": item.name,
                    "created_at": item.created_date_time,
                    "last_modified_date": item.last_modified_date_time,
                }

                files_to_process.append(file_metadata)

        return files_to_process

    except Exception as e:
        logging.error(f"An error occurred retrieving file from SharePoint: {e}")
        return None


def import_file_metadata(files_to_process: list[dict]) -> None:
    """
    Import file metadata into 'data_import' table

    Args:
        files_to_process (list[dict]): List of dictionaries containing file metadata
                                        (file_name, size, created_at, last_modified_date)
    """

    for file_to_download in files_to_process:
        try:
            with Session(engine) as session:
                statement = select(DataImport).where(
                    DataImport.id == file_to_download["id"]
                )
                result = session.exec(statement).first()

                if result is None:
                    result = DataImport(**file_to_download)
                    result.users_status = "pending"
                    result.cards_status = "pending"
                    result.transactions_status = "pending"
                    result.started_at = datetime.datetime.now()

                session.add(result)
                session.commit()

        except Exception as e:
            logging.error(f"An error occurred importing file metadata: {e}")
            continue


def process_data_import_table() -> list[dict]:
    """
    Read data_import table to identify file sources that need to be ingested based on status
    columns

    Returns:
            A list of dictionaries containing file metadata required to be processed
            for ingestion.
    """

    try:
        files_to_download = []

        with Session(engine) as session:
            statement = select(DataImport).where(
                or_(
                    DataImport.users_status != "complete",
                    DataImport.cards_status != "complete",
                    DataImport.transactions_status != "complete",
                )
            )
            results = session.exec(statement)

            for result in results:
                file_metadata = {
                    "id": result.id,
                    "name": result.file_name,
                    "users_status": result.users_status,
                    "cards_status": result.cards_status,
                    "transactions_status": result.transactions_status,
                }

                logging.info(file_metadata)
                files_to_download.append(file_metadata)

        return files_to_download

    except Exception as e:
        logging.error(
            f"An error occurred processing records from data_import table: {e}"
        )


def generate_graph_client() -> GraphServiceClient | None:
    """
    Create instance of Microsoft Graph client

    Returns:
            GraphServiceClient : An instance of Microsoft Graph client required to interact with
                                 Microsoft Teams / SharePoint or None if an error is encountered

    """

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
        return None


async def download_sharepoint_files(files_to_download: list[dict]) -> list[dict] | None:
    """
    Downloads files from Microsoft Teams site / SharePoint

    Args:
        files_to_download (list[dict]): Files metadata from Microsoft Teams / SharePoint containing
                                        the "drive item id's" required to download the files

    Returns:
        list[dict]: A list of dictionaries containing 'name' and 'path' for each
                    successfully downloaded file or None if an error is encountered
    """

    try:
        graph_client = generate_graph_client()

        credential = DefaultAzureCredential()

        vault_url = os.getenv("vault_url")
        secret_client = SecretClient(vault_url=vault_url, credential=credential)

        drive_id = secret_client.get_secret("sharepoint-site-drive-id").value

        file_paths = []

        for file_to_download in files_to_download:
            try:
                users_status = file_to_download["users_status"]
                cards_status = file_to_download["cards_status"]
                transactions_status = file_to_download["transactions_status"]

                logging.info(f"drive_id: {drive_id}")
                drive_item_id = file_to_download["id"]
                logging.info(f"drive_item_id: {drive_item_id}")
                name = file_to_download["name"]

                # Get temp/tmp directory location
                temp_file_path = tempfile.gettempdir()

                file_path = os.path.join(temp_file_path, name)

                download = (
                    await graph_client.drives.by_drive_id(drive_id)
                    .items.by_drive_item_id(drive_item_id)
                    .content.get()
                )

                with open(file_path, "wb") as file:
                    file.write(download)

                file_metadata = {
                    "name": name,
                    "path": file_path,
                    "users_status": users_status,
                    "cards_status": cards_status,
                    "transactions_status": transactions_status,
                }

                file_paths.append(file_metadata)
            except Exception as e:
                logging.error(f"An error occurred downloading file: {name}. {e}")

        return file_paths
    except Exception as e:
        logging.error(f"An error occurred downloading file(s): {e}")
        return None


async def ingest_sharepoint_files(sharepoint_files: list[dict], context: func.Context) -> None:
    """
    Ingest records from xlsx file

    Args:
        sharepoint_files (list[dict]): List of file metadata dictionaries containing 'name' and 'path'
                                       key/value pairs for xlsx files
        context (func.Context): Azure Functions context for logging
    """

    try:
        logging.info(f"Starting import for {len(sharepoint_files)} files.")
        async with asyncio.TaskGroup() as tg:
            for sharepoint_file in sharepoint_files:
                logging.info(f"Creating task for {sharepoint_file['name']}")
                tg.create_task(asyncio.to_thread(process_single_month, sharepoint_file, context))
    except ExceptionGroup as eg:
        for exc in eg.exceptions:
            logging.error(f"Task failed with error: {exc}", exc_info=exc)


def process_single_month(sharepoint_file: dict, context: func.Context) -> None:
    """
    Reads 'users', 'cards', 'transactions' sheets into dataframes, checks status columns in 'data_import'
    table, only processes sheets that not marked as complete in corresponding status column.

    Args:
        sharepoint_file (dict): File metadata dictionary containing 'name' and 'path' key/value pairs
        for xlsx with user, card and transactions data
        context (func.Context): Azure Functions context for logging

    """

    context.thread_local_storage.invocation_id = context.invocation_id

    logging.info(f"Processing {sharepoint_file['name']}...")

    file_path = sharepoint_file["path"]
    file_name = sharepoint_file["name"]

    users_status = sharepoint_file["users_status"]
    cards_status = sharepoint_file["cards_status"]
    transactions_status = sharepoint_file["transactions_status"]

    if users_status != "complete":
        logging.info(f"Initiating import for 'users' from {file_name}...")
        users = pd.read_excel(open(file_path, "rb"), sheet_name="users")
        process_users(users, file_name)

    if cards_status != "complete":
        logging.info(f"Initiating import for 'cards' from {file_name}...")
        cards = pd.read_excel(open(file_path, "rb"), sheet_name="cards")
        process_cards(cards, file_name)

    if transactions_status != "complete":
        logging.info(f"Initiating import for 'transactions' from {file_name}...")
        transactions = pd.read_excel(open(file_path, "rb"), sheet_name="transactions")

        process_transactions(transactions, file_name)

    update_job_finished_at(file_name)


def process_users(users: pd.DataFrame, file_name: str) -> None:
    """
    Iterates over dataframe rows, creating key/value pairs for each row. Rows are then appended to a
    single list of dictionaries ready to be inserted into db.

    Args:
        users (pd.DataFrame): Pandas Dataframe containing users data
        file_name (str): Name of the source file for tracking data origin
    """

    model = Users
    processed_rows = []

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
                "source": file_name,
            }

            processed_rows.append(row_data)

        except Exception as e:
            logging.error(
                f"An error occurred processing {row['id']} record from users sheet: {e}"
            )
            continue

    bulk_insert(processed_rows, model, file_name)


def process_cards(cards: pd.DataFrame, file_name: str) -> None:
    """
    Iterates over dataframe rows, creating key/value pairs for each row. Rows are then appended to a
    single list of dictionaries ready to be inserted into db.

    Args:
        cards (pd.DataFrame): Pandas Dataframe containing cards data
        file_name (str): Name of the source file for tracking data origin
    """

    model = Cards
    processed_rows = []

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
                "source": file_name,
            }

            processed_rows.append(row_data)

        except Exception as e:
            logging.error(
                f"An error occurred processing {row['id']} card record from cards sheet: {e}"
            )
            continue

    bulk_insert(processed_rows, model, file_name)


def process_transactions(transactions: pd.DataFrame, file_name: str) -> None:
    """
     Iterates over dataframe rows, creating key/value pairs for each row. Rows are then appended to a
    single list of dictionaries ready to be inserted into db.

    Args:
        transactions (pd.DataFrame): Pandas Dataframe containing transactions data
        file_name (str): Name of the source file for tracking data origin
    """

    processed_rows = []
    model = Transactions

    for index, row in transactions.iterrows():
        try:
            row_data = {
                "id": row["id"],
                "date": row["date"],
                "client_id": row["client_id"],
                "card_id": row["card_id"],
                "amount": row["amount"],
                "use_chip": row["use_chip"],
                "merchant_id": row["merchant_id"],
                "merchant_city": (
                    None if pd.isna(row["merchant_city"]) else row["merchant_city"]
                ),
                "merchant_state": (
                    None if pd.isna(row["merchant_state"]) else row["merchant_state"]
                ),
                "zip": None if pd.isna(row["zip"]) else row["zip"],
                "mcc": None if pd.isna(row["mcc"]) else row["mcc"],
                "errors": None if pd.isna(row["errors"]) else row["errors"],
                "source": file_name,
            }

            processed_rows.append(row_data)

        except Exception as e:
            logging.error(f"An error occurred processing record {row_data['id']}: {e}")
            continue

    bulk_insert(processed_rows, model, file_name)


def bulk_insert(
    processed_rows: list[dict], model: type[SQLModel], file_name: str
) -> None:
    """
    Bulk insert records into database in batches of 1000

    Args:
        processed_rows (list[dict]): A list of processed dictionaries ready to be inserted into db
        model (type[SQLModel]): SQLModel table class representing the target database table
    """

    status = 0

    batches = len(processed_rows) // 1000
    logging.info(f"Total number of batches to insert for {file_name}: {batches}")

    for batch_index, batch in enumerate(batched(processed_rows, 1000)):
        logging.info(
            f"Inserting batch ({model.__name__}) {batch_index} of {batches} from {file_name}..."
        )

        try:
            with Session(engine) as session:
                session.exec(insert(model), params=batch)
                session.commit()

        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                logging.warning(
                    f"An error occurred inserting {batch_index} of {batches} from {file_name}: {e}"
                )

        except Exception as e:
            logging.error(f"An error occurred inserting batch: {e} ")
            status = 1
            continue

    logging.info(f"Status from processing {file_name}: {status}")

    update_status(file_name, model, status)


def update_status(file_name: str, model: type[SQLModel], status: int):
    """
    Update import status for sheet data imported, status can be 'failed'
    or 'complete'

    Args:
        file_name (str): Name of the source file for tracking data origin
        model (type[SQLModel]): SQLModel table class representing the target database table
        status (int): Status code, 0 represents complete, 1 represents failed
    """

    logging.info(f"Updating status for {file_name}")

    logging.info(f"Model: {model.__name__}")
    logging.info(f"Type: {type(model.__name__)}")
    logging.info(f"Status: {status}")

    model_name = model.__name__

    if model_name == "Transactions":
        logging.info("Model detected is Transactions")
        column = "transactions_status"

    if model_name == "Cards":
        logging.info("Model detected is Cards")
        column = "cards_status"

    if model_name == "Users":
        logging.info("Model detected is Users")
        column = "users_status"

    try:
        with Session(engine) as session:
            statement = select(DataImport).where(DataImport.file_name == file_name)
            result = session.exec(statement).first()

            if status == 0:
                logging.info(
                    f"{model_name} batches from {file_name} were successfully imported."
                )
                logging.info(
                    f"Updating status for {model_name} from {file_name} to 'complete'."
                )

                setattr(result, column, "complete")
            else:
                logging.info(
                    f"{model_name} batches {file_name} were not successfully imported!"
                )
                logging.info(
                    f"Updating status for {model_name} from {file_name} to 'failed'."
                )

                current_status = getattr(result, column)

                if current_status != "complete":
                    setattr(result, column, "failed")

            session.add(result)
            session.commit()
    except Exception as e:
        logging.error(f"An error occurred updating status for {file_name} import: {e}")


def update_job_finished_at(file_name: str):
    """
    Update finished_at time in 'data_import' table for job import.

    Args:
        file_name (str): Name of the source file for tracking data origin
    """

    try:
        with Session(engine) as session:
            statement = select(DataImport).where(DataImport.file_name == file_name)
            result = session.exec(statement).first()

            result.finished_at = datetime.datetime.now()

            session.add(result)
            session.commit()
    except Exception as e:
        logging.error(f"An error occurred updating finished_at time: {e}")
