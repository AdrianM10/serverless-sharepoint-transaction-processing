import pytest
import pandas as pd
import math
import os

from ingest_sharepoint_files_blueprint import process_transactions, process_cards
from models import Transactions, Cards, Users
from sqlmodel import Session, SQLModel, create_engine, select, delete


FILE_PATH = "Sample Financial Transactions Dataset.xlsx"


@pytest.fixture(name="session")
def session_fixture():
    db_password = os.environ.get("DB_PASSWORD", "")
    engine = create_engine(
        f"postgresql://postgres:{db_password}@localhost:5432/transactions"
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def cards_data():
    cards = pd.read_excel(open(FILE_PATH, "rb"), sheet_name="cards")

    return cards


@pytest.fixture
def users_data():
    users = pd.read_excel(open(FILE_PATH, "rb"), sheet_name="users")

    return users


@pytest.fixture
def transactions_data():
    transactions = pd.read_excel(
        open(FILE_PATH, "rb"), sheet_name="transactions")

    return transactions


def test_cards_data(cards_data):
    expected_columns = [
        "id",
        "client_id",
        "card_brand",
        "card_type",
        "card_number",
        "expires",
        "cvv",
        "has_chip",
        "num_cards_issued",
        "credit_limit",
        "acct_open_date",
        "year_pin_last_changed",
        "card_on_dark_web",
    ]

    assert len(cards_data) > 0
    assert len(cards_data.columns) == len(expected_columns)
    assert set(cards_data.columns) == set(expected_columns)


def test_users_data(users_data):
    expected_columns = [
        "id",
        "current_age",
        "retirement_age",
        "birth_year",
        "birth_month",
        "gender",
        "address",
        "latitude",
        "longitude",
        "per_capita_income",
        "yearly_income",
        "total_debt",
        "credit_score",
        "num_credit_cards",
    ]

    assert len(users_data) > 0
    assert len(users_data.columns) == len(expected_columns)
    assert set(users_data.columns) == set(expected_columns)


def test_transactions_data(transactions_data):
    expected_columns = [
        "id",
        "date",
        "client_id",
        "card_id",
        "amount",
        "use_chip",
        "merchant_id",
        "merchant_city",
        "merchant_state",
        "zip",
        "mcc",
        "errors",
    ]

    assert len(transactions_data) > 0
    assert len(transactions_data.columns) == len(expected_columns)
    assert set(transactions_data.columns) == set(expected_columns)


def test_process_transactions(session: Session, transactions_data):

    statement = select(Transactions).where(Transactions.source == FILE_PATH)
    results = session.exec(statement).all()

    assert len(results) == 0

    process_transactions(transactions_data, FILE_PATH)

    statement = select(Transactions).where(Transactions.source == FILE_PATH)
    results = session.exec(statement).all()

    assert len(results) == 5

    # Delete all records that were inserted into table
    session.exec(delete(Transactions).where(Transactions.source == FILE_PATH))
    session.commit()


def test_process_cards(session: Session, cards_data):

    statement = select(Cards).where(Cards.source == FILE_PATH)
    results = session.exec(statement).all()

    assert len(results) == 0

    process_cards(cards_data, FILE_PATH)

    statement = select(Cards).where(Cards.source == FILE_PATH)
    results = session.exec(statement).all()

    assert len(results) == 5

    # Delete all records that were inserted into table
    session.exec(delete(Cards).where(Cards.source == FILE_PATH))
    session.commit()
