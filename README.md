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

- [WIP]

### Prerequisites

- Microsoft Teams Site
- App registration with API permissions (Sites.Selected, Files.Read.All, User.Read.All)


## Usage


## Technologies Used

- Microsoft Graph
- Azure Functions
- Terraform
- PostgreSQL
- Alembic
- SQLModel
- GitHub Actions
- Azure Monitor & Application Insights