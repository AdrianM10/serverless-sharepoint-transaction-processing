from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlmodel import SQLModel

from alembic import context
import urllib.parse
from models import (
    Cards, Transactions, Users, AuditLog, DataImport,
    log_changes_function,
    audit_cards_trigger, audit_transactions_trigger,
    audit_users_trigger, audit_data_import_trigger
)

from alembic_utils.replaceable_entity import register_entities

import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get the URL from alembic.ini and replace placeholders
url = config.get_main_option("sqlalchemy.url")

environment = os.getenv("environment", "local")

if environment in ["azure-dev", "azure-prod"]:

    username = "POSTGRESQL_ADMINS"
    encoded_username = urllib.parse.quote(username, safe="")
    password = os.getenv("DB_PASSWORD", "")
    host = os.environ.get("DB_HOST", "")

    if url:

        url = url.replace("USERNAME", encoded_username).replace(
            "PASSWORD", password).replace("@HOST", host)


else:

    username = "postgres"
    encoded_username = urllib.parse.quote(username, safe="")
    password = os.getenv("DB_PASSWORD", "")
    host = os.environ.get("DB_HOST", "")

    url = url.replace("USERNAME", encoded_username).replace(
            "PASSWORD", password).replace("@HOST", host)
    


config.set_main_option("sqlalchemy.url", url)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Register entities with alembic_utils.
register_entities([log_changes_function,
                   audit_cards_trigger,
                   audit_transactions_trigger,
                   audit_users_trigger,
                   audit_data_import_trigger])


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
