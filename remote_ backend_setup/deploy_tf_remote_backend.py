import os
import logging

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient


def main():

    credential = DefaultAzureCredential()
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    rg_name = "rg-sp-txn-tf-backend"
    location = "southafricanorth"
    storage_account_name = "sptxntfstr"
    blob_container_name = "tfstate"

    rg_name = provision_resource_group(
        credential, subscription_id, rg_name, location)


def provision_resource_group(credential, subscription_id: str, rg_name: str, location: str) -> str:
    """ Creates a resource group in a specified location"""

    try:

        resource_client = ResourceManagementClient(credential, subscription_id)

        rg_result = resource_client.resource_groups.create_or_update(
            rg_name, {"location": location})
        logging.info(
            f"Provisioned resource group {rg_result.name} in the {rg_result.location} region.")

        return rg_result.name
    except Exception as e:
        logging.exception(
            f"An error occurred creating the resource group: {e}")


if __name__ == "__main__":
    main()
