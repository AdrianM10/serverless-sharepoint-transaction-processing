import os
import urllib.parse
from azure.identity import DefaultAzureCredential
from sqlmodel import create_engine


def get_database_engine():
    """
    Create database engine based on environment variable.
    """

    environment = os.getenv("environment", "local")

    if environment in ["azure-dev", "azure-prod"]:

        credential = DefaultAzureCredential()
        token = credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        )
        access_token = token.token

        username = "POSTGRESQL_ADMINS"
        encoded_username = urllib.parse.quote(username, safe="")
        host = os.environ.get("DB_HOST")
        db_name = "transactions"

        connection_string = f"postgresql://{encoded_username}:{host}/{db_name}"

        engine = create_engine(
            connection_string,
            connect_args={"password": access_token},
        )
    else:

        db_password = os.environ.get("DB_PASSWORD")
        engine = create_engine(
            f"postgresql://postgres:{db_password}@localhost:5432/financial_transactions"
        )

    return engine


def get_database_url():
    """
    Get database URL string based on environment (local or Azure)
    """
    environment = os.getenv("environment", "local")

    if environment in ["azure-dev", "azure-prod"]:
        username = "POSTGRESQL_ADMINS"
        encoded_username = urllib.parse.quote(username, safe="")
        host = os.environ.get("DB_HOST")
        return f"postgresql://{encoded_username}:PASSWORD@{host}/transactions"
    else:
        db_password = os.environ.get("DB_PASSWORD", "PASSWORD")
        return f"postgresql://postgres:{db_password}@localhost:5432/financial_transactions"
