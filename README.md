# Overview

This repository contains a serverless file processing backend app using Azure Functions to ingest data stored in a Microsoft Teams site into PostgreSQL. The datasets are monthly xlsx files containing financial transactions for YE2010.

## Repository Structure

- **`github/workflows/`** - GitHub Actions and CI/CD related configurations
- **`database/`** - Migration scripts for database
- **`function_apps/ingest_sharepoint_files/`** - Timer based trigger function app that processes xlsx files from sharepoint and persists data into PostgreSQL
- **`iac/`** - Terraform modules to deploy Azure Functions, PostgreSQL and Key Vault
- **`remote_backend_setup/`** - Python script to deploy remote backend required by Terraform
- **`sample_datasets/`** - Multiple financial transaction datasets


## Getting Started

This project is designed as a learning resource for using Python based Azure Functions to interact with a PostgreSQL database hosted in Azure.

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

[WIP]

## Technologies Used

- Microsoft Graph
- Azure Functions
- Terraform
- PostgreSQL
- Alembic
- SQLModel
- GitHub Actions
- Azure Monitor & Application Insights