import logging
import os

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient


def main():

    credential = DefaultAzureCredential()
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    rg_name = "rg-sp-txn-tf-backend"
    location = "southafricanorth"
    storage_account_name = "sptxntfstr"
    blob_container_name = "tfstate"

    rg_name = provision_resource_group(credential, subscription_id, rg_name, location)

    provision_storage_account(
        credential,
        subscription_id,
        storage_account_name,
        rg_name,
        location,
        blob_container_name,
    )


def provision_resource_group(
    credential, subscription_id: str, rg_name: str, location: str
) -> str:
    """Creates a resource group in a specified location"""

    try:

        resource_client = ResourceManagementClient(credential, subscription_id)

        rg_result = resource_client.resource_groups.create_or_update(
            rg_name, {"location": location}
        )
        logging.info(
            f"Provisioned resource group {rg_result.name} in the {rg_result.location} region."
        )

        return rg_result.name
    except Exception as e:
        logging.exception(f"An error occurred creating the resource group: {e}")


def provision_storage_account(
    credential,
    subscription_id: str,
    storage_account_name: str,
    rg_name: str,
    location: str,
    blob_container_name: str,
):
    """Create storage account and blob container"""

    try:

        storage_client = StorageManagementClient(credential, subscription_id)

        # Check availability of storage account name
        availability_result = storage_client.storage_accounts.check_name_availability(
            {"name": storage_account_name}
        )

        if not availability_result.name_available:
            logging.warning(
                f"Storage name {storage_account_name} is already in use. Try another name"
            )

        poller = storage_client.storage_accounts.begin_create(
            rg_name,
            storage_account_name,
            {
                "location": location,
                "kind": "StorageV2",
                "sku": {"name": "Standard_LRS"},
            },
        )

        account_result = poller.result()
        logging.info(f"Provisioned storage account {account_result.name}")

    except Exception as e:
        logging.exception(f"An error occurred creating storage account: {e}")

    try:
        container_name = blob_container_name
        container = storage_client.blob_containers.create(
            rg_name, storage_account_name, container_name, {}
        )
        logging.info(f"Provisioned blob container: {container_name}")
        logging.info(container)

    except Exception as e:
        logging.exception(f"An error occurred creating blob container: {e}")


if __name__ == "__main__":
    main()
