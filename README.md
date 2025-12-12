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

This project is designed as a learning resource for using Python based Azure Functions to interact with PostgreSQL database hosted in Azure.

### Prerequisites

- Azure subscription with Owner permissions
- Privileged Role Administrator (Entra role)


### Register an app in Entra

1. Sign into the Azure Portal.
2. Search for "Microsoft Entra ID" in the main search bar.
3. Select "App registrations" under "Manage".
4. Select "New registration" on the menu bar.
5. Enter a name for the app, i.e "Teams-Site-Reader-App", select Register at the bottom of the page.
6. Navigate towards "API permissions" under "Manage".
7. Select "Add a permission".
8. Select the "Microsoft Graph" widget, select "Application permissions".
9. Assign the below permissions:

    - Sites.Selected
    - Files.Read.All
    - User.Read.All

10. Navigate towards "Certificates & secrets", select "New client secret", enter a description and select a suitable expiry from the dropdown. Select "Add".
11. Store the secret value in a password manager i.e "1Password" or Azure Key Vault if you have one setup already. This value will not be shown again if you leave the page.
12. Grant admin consent for the newly added permissions.

### Microsoft Teams Site setup

[WIP]

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