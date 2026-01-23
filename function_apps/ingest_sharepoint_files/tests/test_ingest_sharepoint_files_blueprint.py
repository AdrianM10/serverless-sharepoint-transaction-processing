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
from faker_credit_score import CreditScore


from faker import Faker

fake = Faker()
fake.add_provider(CreditScore)


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
    transactions = pd.read_excel(open(FILE_PATH, "rb"), sheet_name="transactions")

    return transactions


@pytest.fixture
def generate_cards_data():
    def number_of_cards_to_generate(number_of_cards):
        generated_cards = []

        for _ in range(number_of_cards):
            data = {
                "id": fake.unique.numerify("####"),
                "client_id": fake.numerify("####"),
                "card_brand": fake.credit_card_provider(),
                "card_type": random.choice(["credit", "debit"]),
                "card_number": fake.credit_card_number(),
                "expires": fake.credit_card_expire(date_format="%Y/%m/%d"),
                "cvv": fake.credit_card_security_code(),
                "has_chip": random.choice(["YES", "NO"]),
                "num_cards_issued": random.randint(1, 3),
                "credit_limit": random.randrange(1000, 150000),
                "acct_open_date": fake.date(pattern="%Y/%m/%d"),
                "year_pin_last_changed": fake.year(),
                "card_on_dark_web": random.choice(["Yes", "No"]),
                "source": FILE_PATH,
            }

            generated_cards.append(data)

        return generated_cards

    return number_of_cards_to_generate


@pytest.fixture
def generate_users_data():
    def number_of_users_to_generate(number_of_users):
        generated_users = []

        for _ in range(number_of_users):
            data = {
                "id": fake.unique.numerify("####"),
                "current_age": random.randint(18, 100),
                "retirement_age": random.randint(50, 79),
                "birth_year": fake.year(),
                "birth_month": fake.month(),
                "gender": random.choice(["Male", "Female"]),
                "address": fake.address(),
                "latitude": fake.latitude(),
                "longitude": fake.longitude(),
                "per_capita_income": random.randint(0, 163145),
                "yearly_income": random.randint(50000, 200000),
                "total_debt": random.randint(10000, 45000),
                "credit_score": fake.credit_score(),
                "num_credit_cards": random.randint(1, 9),
                "source": FILE_PATH,
            }

            generated_users.append(data)

        return generated_users

    return number_of_users_to_generate


@pytest.fixture
def generate_transactions_data():
    def number_of_transactions_to_generate(number_of_transactions):
        generated_transactions = []

        for _ in range(number_of_transactions):
            data = {
                "id": fake.unique.numerify("#######"),
                "date": fake.iso8601(),
                "client_id": fake.numerify("####"),
                "card_id": fake.numerify("####"),
                "amount": fake.pyfloat(min_value=-500, max_value=1900),
                "use_chip": random.choice(["Online Transaction", "Swipe Transaction"]),
                "merchant_id": fake.unique.numerify("######"),
                "merchant_city": fake.city(),
                "merchant_state": fake.country(),
                "zip": fake.zipcode(),
                "mcc": fake.numerify("####"),
                "errors": random.choice(
                    [
                        "",
                        "Bad Card Number",
                        "Bad Card Number,Bad CVV",
                        "Bad Card Number,Bad Expiration",
                        "Bad Card Number,Insufficient Balance",
                        "Bad CVV",
                        "Bad CVV,Insufficient Balance",
                        "Bad CVV,Technical Glitch",
                        "Bad Expiration",
                        "Technical Glitch",
                    ]
                ),
                "source": FILE_PATH,
            }

            generated_transactions.append(data)

        return generated_transactions

    return number_of_transactions_to_generate


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


class TestProcessUsers:
    def test_process_users(self, session: Session, users_data):
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

    def test_large_number_of_users(self, session: Session, generate_users_data):
        number_of_users = 2000

        users = pd.DataFrame(generate_users_data(number_of_users))

        process_users(users, FILE_PATH)
        statement = select(Users).where(Users.source == FILE_PATH)
        results = session.exec(statement).all()

        assert len(results) == len(users)

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


class TestProcessTransactions:
    def test_process_transactions(self, session: Session, transactions_data):
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

    def test_large_number_of_transactions(
        self, session: Session, generate_transactions_data
    ):
        number_of_transactions = 100000

        transactions = pd.DataFrame(generate_transactions_data(number_of_transactions))

        process_transactions(transactions, FILE_PATH)
        statement = select(Transactions).where(Transactions.source == FILE_PATH)
        results = session.exec(statement).all()

        assert len(results) == len(transactions)

        session.exec(delete(Transactions).where(Transactions.source == FILE_PATH))
        session.commit()
