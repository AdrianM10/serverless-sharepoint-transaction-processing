import pytest
import pandas as pd
import math
import os
import random

from ingest_sharepoint_files_blueprint import (
    process_transactions,
    process_cards,
    process_users,
    bulk_insert,
)
from models import Transactions, Cards, Users
from sqlmodel import Session, SQLModel, create_engine, select, delete


from faker import Faker

fake = Faker()


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


@pytest.fixture
def generate_cards_data():

    def number_of_cards_to_generate(number_of_cards):

        generated_cards = []

        for _ in range(number_of_cards):

            data = {
                "id": fake.numerify("####"),
                "client_id": fake.numerify("####"),
                "brand": fake.credit_card_provider(),
                "card_type": random.choice(["credit", "debit"]),
                "credit_card_number": fake.credit_card_number(),
                "expiry_date": fake.credit_card_expire(date_format='%Y/%m/%d'),
                "cvv": fake.credit_card_security_code(),
                "has_chip": random.choice(["YES", "NO"]),
                "num_cards_issued": random.randint(1, 3),
                "credit_limit": random.randrange(1000, 150000),
                "acct_open_date": fake.date(pattern="%Y/%m/%d"),
                "year_pin_last_changed": fake.year(),
                "card_on_dark_web": random.choice(["Yes", "No"])
            }

            generated_cards.append(data)

        return generated_cards
    
    return number_of_cards_to_generate


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


def test_process_users(session: Session, users_data):
    statement = select(Users).where(Users.source == FILE_PATH)
    results = session.exec(statement).all()

    assert len(results) == 0
    process_users(users_data, FILE_PATH)
    statement = select(Users).where(Users.source == FILE_PATH)
    results = session.exec(statement).all()

    assert len(results) == 5

    # Delete all records from table post assert
    session.exec(delete(Users).where(Users.source == FILE_PATH))
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


def test_bulk_insert(session: Session, generate_cards_data):

    number_of_cards = 10000

    assert len(generate_cards_data(number_of_cards)) == number_of_cards

