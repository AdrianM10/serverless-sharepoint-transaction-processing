# Overview

This repository contains a serverless file processing backend app using Azure Functions to ingest data stored in a Microsoft Teams site into PostgreSQL. The datasets are monthly xlsx files containing financial transactions for YE2010.


## Repository Structure

- **`github/workflows/`** - GitHub Actions and CI/CD related configurations
- **`database/`** - Migration scripts for database
- **`function_apps/ingest_sharepoint_files/`** - Timer based trigger function app that processes xlsx files from sharepoint and persists data into PostgreSQL
- **`iac/`** - Terraform modules to deploy Azure Functions, PostgreSQL, Virtual Network and Key Vault
- **`remote_backend_setup/`** - Python script to deploy remote backend required by Terraform
- **`sample_datasets/`** - Multiple financial transaction datasets


## Getting Started

This project is a serverless data processing pipeline built using Azure Functions. It demonstrates automated ingestion of financial transaction data from SharePoint into PostgreSQL. Infrastructure management and database migrations are handled through CI/CD.

### Prerequisites

- Azure subscription with Owner permissions
- Privileged Role Administrator (Entra role)


### Register an app in Entra

1. Sign into the Azure Portal.
2. Search for **Microsoft Entra ID** in the main search bar.
3. Select **App registrations** under **Manage**.
4. Select **New registration** on the menu bar.
5. Enter a name for the app, i.e **Teams-Site-Reader-App**, select Register at the bottom of the page.
6. Navigate towards **API permissions** under **Manage**.
7. Select **Add a permission**.
8. Select the **Microsoft Graph** widget, select **Application permissions**.
9. Assign the below permissions:

    - Sites.Selected
    - Files.Read.All
    - User.Read.All

10. Navigate towards **Certificates & secrets**, select **New client secret**, enter a description and select a suitable expiry from the dropdown. Select **Add**.
11. Store the secret value in a password manager i.e **1Password** or Azure Key Vault if you have one setup already. This value will not be shown again if you leave the page.
12. Grant admin consent for the newly added permissions.

### Microsoft Teams Site setup

1. Open Microsoft Teams, select **New team**. Enter **Financial Transactions** as the name and **General** as the name for the first channel.
2. Navigate towards the newly created Team and upload the **Transactions** directory contained within the **sample_datasets** directory within this repository.
3. Within the newly created channel (General), select the **Shared** tab, select **Open in SharePoint** from the menu bar.
4. Select **Home** from the left-hand side menu, append **/_api/site/id** to the url.
5. Store the **Edm.Guid** value, this guid is the **site id** which will require you to grant permissions via the Graph Explorer tool.
6. Open a new tab, navigate towards **https://developer.microsoft.com/en-us/graph/graph-explorer**.
7. Sign in and accept the permissions requested pop-up.
8. Enter the below url, replace the site id with the site id you retrieved in **step 5**:

```http
    https://graph.microsoft.com/v1.0/sites/{{ Site Id }}/permissions
```

9. Paste the below payload in the request body, populate the **id** and **displayName** values with values from the app you created earlier, the values can be retrieved from overview page of the app.

```json
{
    "roles": [
        "read"
    ],
    "grantedToIdentities": [
        {
            "application": {
                "id": "{{ App Id }}",
                "displayName": "{{ App Display Name}}"
            }
        }
    ]
}
```

10. Change the method to **POST** and select **Run query**.

11. If you receive a **403** error, your signed in user will need permissions to perform the operation, select the **Modify Permissions** tab and consent to the **Sites.FullControl.All** permissions.

## Usage

1. Fork this repository to your own account.
2. Create a security group in Entra named **POSTGRESQL_ADMINS**.
3. [Configure OpenID Connect in Azure](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure).
4. Create and populate repository secrets, see **Repository secrets** section for required secrets.
5. Navigate towards the **Actions** tab, select **Deploy terraform backend** and select **Run workflow** on the main branch.
6. Under **All workflows**, select **Deploy Serverless Financial Transactions Processing App**.
7. Select **Run workflow**, select **yes** under the **Deploy infrastructure (y/n) ?**, ensure **no** is set under **Perform database migration (y/n) ?**.  
8. Wait for the infrastructure deployment to complete successfully. This will provision Azure Functions, PostgreSQL database, Virtual Network as well as the Azure Key Vault.
9. Once the infrastructure has been deployment run the workflow again, this time select **no** for the infrastructure deployment and **yes** for the database migration to apply the alembic schema migrations.

Note: Infrastructure deployment and database migrations are separate operations.

- **Infrastructure deployment** - Use when deploying new resources, updating Terraform configurations or deploying function (app) code changes.

- **Database migration** - Use when applying alembic schema changes to database.

## Repository secrets

Create and populate the below repository secrets:

- **ALERT_CONFIG** - Contact info for environment specific alerts.

```
{

  dev = {
    contact_name  = "Dev Support"
    contact_email = "dev@example.com"
  }
  prod = {
    contact_name  = "Prod Support"
    contact_email = "prod@example.com"
  }

}
```

- **AZURE_CLIENT_ID** - Application (client) ID from the federated credential app registration
- **AZURE_SUBSCRIPTION_ID** -  Azure subscription ID where resources will be deployed
- **AZURE_TENANT_ID** - Microsoft Entra tenant ID

- **IP_ADDRESS** - Your public IP address to be whitelisted on the firewall rule.
- **POSTGRESQL_ADMINS_OBJECT_ID** - Entra security group object ID
- **PSQL_SERVER_NAME** - A unique name that identifies your Azure Database for PostgreSQL flexible server instance
- **DB_HOST** - Fully Qualified Domain Name for PostgreSQL flexible server instance, format:

```
@{{PSQL_SERVER_NAME}}-postgresqlserver.postgres.database.azure.com:5432
```
- **STORAGE_ACCOUNT_NAME** - Globally unique name for Storage Account resource to be created.
- **KV_NAME** - Globally unique name for Azure Key Vault resource to be created.
- **VAULT_URL_DEV** - Azure Key Vault URI, format:

``` 
https://{{KV_NAME}}.vault.azure.net/
```




## Technologies Used

- Microsoft Graph
- Azure Functions
- Terraform
- PostgreSQL
- Alembic
- SQLModel
- GitHub Actions
- Azure Monitor & Application Insights