import os
import urllib.parse
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from azure.identity import DefaultAzureCredential
from sqlalchemy import BigInteger, SmallInteger
from sqlmodel import Column, Field, SQLModel, create_engine, select, insert


class Cards(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    client_id: int
    card_brand: str
    card_type: str
    card_number: str
    expires: date
    cvv: int = Field(default=None, sa_column=Column(SmallInteger()))
    has_chip: str
    num_cards_issued: int = Field(
        default=None, sa_column=Column(SmallInteger()))
    credit_limit: int = Field(default=None, sa_column=Column(BigInteger()))
    acct_open_date: date
    year_pin_last_changed: int = Field(
        default=None, sa_column=Column(SmallInteger()))
    card_on_dark_web: str
    source: Optional[str] | None = None


class Transactions(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: date
    client_id: int = Field(default=None, sa_column=Column(SmallInteger()))
    card_id: int = Field(default=None, sa_column=Column(SmallInteger()))
    amount: Decimal = Field(default=0, max_digits=18, decimal_places=2)
    use_chip: str
    merchant_id: int
    merchant_city: Optional[str] | None = None
    merchant_state: Optional[str] | None = None
    zip: Optional[int] | None = None
    mcc: Optional[int] | None = None
    errors: Optional[str] | None = None
    source: Optional[str] | None = None


class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    current_age: int | None = Field(
        default=None, sa_column=Column(SmallInteger()))
    retirement_age: int | None = Field(
        default=None, sa_column=Column(SmallInteger()))
    birth_year: int | None = Field(
        default=None, sa_column=Column(SmallInteger()))
    birth_month: int | None = Field(
        default=None, sa_column=Column(SmallInteger()))
    gender: str
    address: str
    latitude: Decimal = Field(default=0, max_digits=18, decimal_places=2)
    longitude: Decimal = Field(default=0, max_digits=18, decimal_places=2)
    per_capita_income: int
    yearly_income: int
    total_debt: int
    credit_score: int = Field(default=None, sa_column=Column(BigInteger()))
    num_credit_cards: int = Field(
        default=None, sa_column=Column(SmallInteger()))
    source: Optional[str] | None = None

class DataImport(SQLModel, table=True):
    __tablename__ = "data_import"
    id: str | None = Field(default=None, primary_key=True)
    file_name: str
    size: int = Field(default=None, sa_column=Column(BigInteger()))
    created_at: Optional[datetime] | None = None
    last_modified_date: Optional[datetime] | None = None
    started_at: Optional[datetime] | None = None
    finished_at: Optional[datetime] | None = None
    users_status: Optional[str] | None = None
    cards_status: Optional[str] | None = None
    transactions_status: Optional[str] | None = None

db_password = os.environ.get("DB_PASSWORD")

# For Postgres running locally use below
engine = create_engine(
    f"postgresql://postgres:{db_password}@localhost:5432/financial_transactions"
)

# For Postgres running in Azure and using token based auth
# credential = DefaultAzureCredential()
# token = credential.get_token(
#     "https://ossrdbms-aad.database.windows.net/.default")
# access_token = token.token

# username = "POSTGRESQL_ADMINS"
# encoded_username = urllib.parse.quote(username, safe="")
# host = os.environ.get("DB_HOST")
# db_name = "transactions"

# connection_string = f"postgresql://{encoded_username}:{host}/{db_name}"

# engine = create_engine(
#     connection_string,
#     connect_args={
#         "password": access_token,
#     },
# )
