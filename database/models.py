import os
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, SmallInteger
from sqlmodel import Column, Field, SQLModel, create_engine, select


class Cards(SQLModel, table=True):
    id: uuid.UUID | None = Field(primary_key=True)
    client_id: int
    card_brand: str
    card_type: str
    card_number: str
    expires: date
    cvv: int = Field(default=None, sa_column=Column(SmallInteger()))
    has_chip: str
    num_cards_issued: int = Field(default=None, sa_column=Column(SmallInteger()))
    credit_limit : int = Field(default=None, sa_column=Column(BigInteger()))
    acct_open_date: date
    year_pin_last_changed: int = Field(default=None, sa_column=Column(SmallInteger()))
    card_on_dark_web: str



db_password = os.environ.get("DB_PASSWORD")

engine = create_engine(
    f"postgresql://postgres:{db_password}@localhost:5432/financial_transactions"
)
